import os
import tempfile
import time
import uuid
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import requests
import json
import urllib.request
import socket
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# 导入语音识别模块
from baidu_speech import transcribe_with_baidu
try:
    from vosk_speech import transcribe_with_vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk 未安装，将不能使用离线语音识别")

try:
    from xunfei_speech import transcribe_with_xunfei
    XUNFEI_AVAILABLE = True
except ImportError:
    XUNFEI_AVAILABLE = False
    print("科大讯飞HTTP模块导入失败")

try:
    from xunfei_websocket import transcribe_with_xunfei_websocket
    XUNFEI_WS_AVAILABLE = True
except ImportError:
    XUNFEI_WS_AVAILABLE = False
    print("科大讯飞WebSocket模块导入失败")

try:
    from xunfei_official import transcribe_with_xunfei_official
    XUNFEI_OFFICIAL_AVAILABLE = True
except ImportError:
    XUNFEI_OFFICIAL_AVAILABLE = False
    print("科大讯飞官方WebSocket模块导入失败")

try:
    from whisper_transcribe import transcribe_with_whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper模块导入失败")

try:
    from whisper_cli import transcribe_with_whisper_cli
    WHISPER_CLI_AVAILABLE = True
except ImportError:
    WHISPER_CLI_AVAILABLE = False
    print("Whisper CLI模块导入失败")

# Load environment variables from .env file
load_dotenv()

# 设置代理（如果需要）
PROXY_URL = os.getenv("PROXY_URL", "")
if PROXY_URL:
    # 为 urllib 设置代理
    proxy_handler = urllib.request.ProxyHandler({
        'http': PROXY_URL,
        'https': PROXY_URL
    })
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)

    # 为 requests 设置代理
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL

    print(f"已设置代理: {PROXY_URL}")

# 语音识别服务选择
# 可选值: google, baidu, vosk, xunfei, xunfei_ws, xunfei_official, whisper, whisper_cli
SPEECH_RECOGNITION_SERVICE = os.getenv("SPEECH_RECOGNITION_SERVICE", "xunfei_official" if XUNFEI_OFFICIAL_AVAILABLE else "whisper_cli" if WHISPER_CLI_AVAILABLE else "whisper" if WHISPER_AVAILABLE else "xunfei_ws" if XUNFEI_WS_AVAILABLE else "xunfei" if XUNFEI_AVAILABLE else "vosk" if VOSK_AVAILABLE else "baidu").lower()

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
# 直接在这里设置你的 API 密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-a74d9a6d8d204890a5ef7efc6a70ec46")

# 设置密钥用于会话
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_development')

# 数据库设置
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')

# 处理进度跟踪
processing_tasks = {}  # 格式: {task_id: {'status': '状态', 'progress': 百分比, 'message': '消息'}}

# 创建数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建使用历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_text TEXT,
        summary TEXT,
        keywords_and_framework TEXT,
        test_questions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 创建对话记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usage_history_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usage_history_id) REFERENCES usage_history(id)
    )
    ''')

    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file"""
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(temp_audio.name, codec='pcm_s16le')
    return temp_audio.name

def transcribe_audio(audio_path):
    """Convert audio to text using speech recognition"""

    # 根据配置选择语音识别服务
    if SPEECH_RECOGNITION_SERVICE == "xunfei_official" and XUNFEI_OFFICIAL_AVAILABLE:
        print("使用科大讯飞官方WebSocket语音识别服务")
        return transcribe_with_xunfei_official(audio_path)
    elif SPEECH_RECOGNITION_SERVICE == "whisper_cli" and WHISPER_CLI_AVAILABLE:
        print("使用Whisper CLI语音识别服务")
        return transcribe_with_whisper_cli(audio_path, model_size="tiny", language="zh", to_simplified=True)
    elif SPEECH_RECOGNITION_SERVICE == "whisper" and WHISPER_AVAILABLE:
        print("使用OpenAI Whisper离线语音识别服务")
        return transcribe_with_whisper(audio_path, model_size="small", language="Chinese", to_simplified=True)
    elif SPEECH_RECOGNITION_SERVICE == "xunfei_ws" and XUNFEI_WS_AVAILABLE:
        print("使用科大讯飞WebSocket语音识别服务")
        return transcribe_with_xunfei_websocket(audio_path)
    elif SPEECH_RECOGNITION_SERVICE == "xunfei" and XUNFEI_AVAILABLE:
        print("使用科大讯飞HTTP语音识别服务")
        return transcribe_with_xunfei(audio_path)
    elif SPEECH_RECOGNITION_SERVICE == "baidu":
        print("使用百度语音识别服务")
        return transcribe_with_baidu(audio_path)
    elif SPEECH_RECOGNITION_SERVICE == "vosk" and VOSK_AVAILABLE:
        print("使用Vosk离线语音识别服务")
        return transcribe_with_vosk(audio_path)

    # 使用 Google 语音识别服务作为备选
    print("使用Google语音识别服务")
    recognizer = sr.Recognizer()

    # 调整识别器参数，提高识别率
    recognizer.energy_threshold = 300  # 能量阈值，越低越敏感
    recognizer.dynamic_energy_threshold = True  # 动态能量阈值
    recognizer.pause_threshold = 0.8  # 停顿阈值，越低越敏感

    with sr.AudioFile(audio_path) as source:
        # 调整音量
        audio_data = recognizer.record(source)

        # 尝试使用Google的语音识别服务
        try:
            # 尝试不同的语言设置
            try:
                text = recognizer.recognize_google(audio_data, language='zh-CN')
                return text
            except:
                # 如果中文识别失败，尝试自动检测语言
                text = recognizer.recognize_google(audio_data)
                return text + "\n(注：使用了自动语言检测)"
        except sr.UnknownValueError:
            print("Google语音识别无法识别音频内容")
            return "无法识别音频内容。请确保音频清晰并包含语音。"
        except sr.RequestError as e:
            print(f"无法连接到Google语音识别服务: {e}")
            return "无法连接到语音识别服务。请检查网络连接，或稍后再试。\n\n可能的原因：\n1. 网络连接问题\n2. 服务器防火墙限制\n3. 区域限制\n4. API使用限制"

def summarize_with_deepseek(text):
    """Use DeepSeek API to summarize the text"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",  # Replace with the appropriate model name
        "messages": [
            {"role": "system", "content": "你是一个专业的内容总结助手。请对以下内容进行简洁、全面的总结归纳，提取关键信息和主要观点。"},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"调用DeepSeek API时出错: {str(e)}"

def generate_keywords_and_framework(text, summary):
    """Use DeepSeek API to generate keywords and framework"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    prompt = f"""
请根据以下内容，提取5-10个关键词，并分析内容的大致框架结构。
不需要总结内容，只需要提取关键词和分析框架结构。

注意：由于语音转文字可能存在错误，请不要从中提取专业名词或生僻词汇。
请专注于提取内容中明确的主题和概念，避免使用可能是转录错误的词语。

原文内容：
{text}

内容总结：
{summary}

请按以下格式输出：
## 关键词
- 关键词1
- 关键词2
- ...

## 内容框架
1. 第一部分：...
2. 第二部分：...
...
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的内容分析助手，擅长提取关键词和分析内容框架。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"生成关键词和框架时出错: {str(e)}"

def generate_test_questions(text, summary, keywords_and_framework):
    """Generate test questions based on the content"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    prompt = f"""
请根据以下内容，生成5个测试问题，用于测试用户对内容的理解。
问题应该涵盖内容的主要概念和关键点，难度适中。

注意：由于语音转文字可能存在错误，请不要基于可能是转录错误的内容提问。
请专注于内容中明确的主题和概念。

原文内容：
{text}

内容总结：
{summary}

关键词和框架：
{keywords_and_framework}

请按以下格式输出5个问题：
1. 问题1
2. 问题2
3. 问题3
4. 问题4
5. 问题5
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的教育测试助手，擅长根据内容生成有针对性的测试问题。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"生成测试问题时出错: {str(e)}"

# 用户认证相关函数
def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, hashed_password))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

# 历史记录相关函数
def save_usage_history(user_id, filename, original_text, summary, keywords_and_framework, test_questions):
    """保存使用历史到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO usage_history
        (user_id, filename, original_text, summary, keywords_and_framework, test_questions)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, filename, original_text, summary, keywords_and_framework, test_questions))
        conn.commit()
        history_id = cursor.lastrowid
        success = True
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        history_id = None
        success = False
    conn.close()
    return success, history_id

def save_chat_message(usage_history_id, role, content):
    """保存聊天消息到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO chat_history
        (usage_history_id, role, content)
        VALUES (?, ?, ?)
        """, (usage_history_id, role, content))
        conn.commit()
        success = True
    except Exception as e:
        print(f"保存聊天消息失败: {e}")
        success = False
    conn.close()
    return success

def get_user_history(user_id):
    """获取用户的使用历史"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, filename, summary, created_at
    FROM usage_history
    WHERE user_id = ?
    ORDER BY created_at DESC
    """, (user_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_history_detail(history_id):
    """获取历史记录的详细信息"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取历史记录详情
    cursor.execute("""
    SELECT * FROM usage_history WHERE id = ?
    """, (history_id,))
    history = dict(cursor.fetchone()) if cursor.fetchone() else None

    if history:
        # 获取聊天记录
        cursor.execute("""
        SELECT role, content, created_at
        FROM chat_history
        WHERE usage_history_id = ?
        ORDER BY created_at ASC
        """, (history_id,))
        chat_history = [dict(row) for row in cursor.fetchall()]
        history['chat_history'] = chat_history

    conn.close()
    return history

# 用户认证路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))

        return render_template('login_new.html', error='用户名或密码不正确')

    return render_template('login_new.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password:
            return render_template('register_new.html', error='用户名和密码不能为空')

        if password != confirm_password:
            return render_template('register_new.html', error='两次输入的密码不一致')

        if create_user(username, password):
            return redirect(url_for('login'))
        else:
            return render_template('register_new.html', error='用户名已存在')

    return render_template('register_new.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# 处理进度API
@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    if task_id in processing_tasks:
        return jsonify(processing_tasks[task_id])
    return jsonify({'status': 'unknown', 'progress': 0, 'message': '任务不存在'})

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401

    data = request.json
    if not data or 'message' not in data or 'context' not in data:
        return jsonify({"error": "缺少必要参数"}), 400

    user_message = data['message']
    context = data['context']

    # 获取原始文本、摘要和测试问题
    original_text = context.get('original_text', '')
    summary = context.get('summary', '')
    test_questions = context.get('test_questions', '')
    history_id = context.get('history_id', None)

    # 构建聊天历史
    chat_history = data.get('chat_history', [])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    prompt = f"""
你是一个教育助手，正在与用户进行关于以下内容的对话。
你的任务是帮助用户理解内容，回答他们的问题，并测试他们的理解。

原文内容：
{original_text}

内容摘要：
{summary}

测试问题：
{test_questions}

请注意：
1. 你只能基于上述内容回答问题，不要引入外部知识
2. 如果用户问的问题超出了上述内容范围，请礼貌地告诉他们你只能回答与上述内容相关的问题
3. 你可以使用测试问题来测试用户的理解，但也可以根据用户的问题生成新的相关问题
4. 保持回答简洁、清晰，避免过长的解释

聊天历史：
"""

    # 添加聊天历史
    for message in chat_history:
        role = "用户" if message['role'] == 'user' else "助手"
        prompt += f"{role}: {message['content']}\n"

    # 添加当前用户消息
    prompt += f"用户: {user_message}\n助手: "

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的教育助手，帮助用户理解内容并测试他们的知识。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        ai_response = result["choices"][0]["message"]["content"]

        # 如果有历史记录ID，保存聊天记录到数据库
        if history_id:
            # 保存用户消息
            save_chat_message(history_id, 'user', user_message)
            # 保存AI回复
            save_chat_message(history_id, 'assistant', ai_response)

        return jsonify({
            "response": ai_response
        })
    except Exception as e:
        return jsonify({"error": f"AI回复出错: {str(e)}"}), 500

# 首页路由
@app.route('/')
def home():
    return render_template('home_new.html', username=session.get('username') if 'user_id' in session else None)

# 使用界面路由
@app.route('/app')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index_new.html', username=session.get('username'))

# 个人中心路由
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 获取用户信息
    user_id = session.get('user_id')
    username = session.get('username')

    # 从数据库获取用户信息
    import datetime

    # 获取用户注册时间
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    register_time = user_data['created_at'] if user_data else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取使用历史
    cursor.execute("SELECT COUNT(*) as count FROM usage_history WHERE user_id = ?", (user_id,))
    usage_data = cursor.fetchone()
    usage_count = usage_data['count'] if usage_data else 0

    # 计算加入天数
    try:
        register_date = datetime.datetime.strptime(register_time, '%Y-%m-%d %H:%M:%S')
    except:
        register_date = datetime.datetime.strptime(register_time, '%Y-%m-%d %H:%M:%S.%f')
    join_days = (datetime.datetime.now() - register_date).days

    # 获取上次使用时间
    cursor.execute("SELECT created_at FROM usage_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    last_usage_data = cursor.fetchone()
    last_usage = last_usage_data['created_at'].split(' ')[0] if last_usage_data else '暂无记录'

    # 获取使用历史
    history = get_user_history(user_id)

    conn.close()

    return render_template('profile.html',
                          username=username,
                          user_id=user_id,
                          register_time=register_time,
                          usage_count=usage_count,
                          join_days=join_days,
                          last_usage=last_usage,
                          history=history)

# 历史记录详情页面
@app.route('/history/<int:history_id>')
def history_detail(history_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    username = session.get('username')

    # 获取历史记录详情
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 确认该历史记录属于当前用户
    cursor.execute("SELECT user_id FROM usage_history WHERE id = ?", (history_id,))
    record = cursor.fetchone()

    if not record or record['user_id'] != user_id:
        conn.close()
        return redirect(url_for('profile'))

    # 获取历史记录详情
    cursor.execute("""
    SELECT * FROM usage_history WHERE id = ?
    """, (history_id,))
    history = dict(cursor.fetchone())

    # 获取聊天记录
    cursor.execute("""
    SELECT role, content, created_at
    FROM chat_history
    WHERE usage_history_id = ?
    ORDER BY created_at ASC
    """, (history_id,))
    chat_history = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template('history_detail.html',
                          username=username,
                          history=history,
                          chat_history=chat_history)

# 清空历史记录路由
@app.route('/clear_history')
def clear_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    # 从数据库中删除用户的历史记录
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 首先获取所有历史记录ID
    cursor.execute("SELECT id FROM usage_history WHERE user_id = ?", (user_id,))
    history_ids = [row[0] for row in cursor.fetchall()]

    # 删除相关的聊天记录
    for history_id in history_ids:
        cursor.execute("DELETE FROM chat_history WHERE usage_history_id = ?", (history_id,))

    # 删除历史记录
    cursor.execute("DELETE FROM usage_history WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('profile'))

# 文件上传处理
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    # 创建任务ID
    task_id = str(uuid.uuid4())
    processing_tasks[task_id] = {
        'status': 'starting',
        'progress': 0,
        'message': '正在准备处理...'
    }

    # 返回任务ID，前端将使用此ID查询进度
    return jsonify({"task_id": task_id})

@app.route('/process/<task_id>', methods=['GET'])
def process_file(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "请先登录"}), 401

    if task_id not in processing_tasks:
        return jsonify({"error": "任务不存在"}), 404

    # 获取上传的文件信息
    file_info = request.args.get('file')
    if not file_info:
        return jsonify({"error": "缺少文件信息"}), 400

    try:
        # 开始处理
        processing_tasks[task_id]['status'] = 'processing'
        processing_tasks[task_id]['progress'] = 5
        processing_tasks[task_id]['message'] = '正在处理文件...'

        # 检查文件类型并处理
        if allowed_file(file_info, ALLOWED_AUDIO_EXTENSIONS):
            # 处理音频文件
            processing_tasks[task_id]['progress'] = 10
            processing_tasks[task_id]['message'] = '正在处理音频文件...'

            audio_path = os.path.join(UPLOAD_FOLDER, file_info)

            # 转换为WAV格式（如果需要）
            if not audio_path.endswith('.wav'):
                processing_tasks[task_id]['progress'] = 15
                processing_tasks[task_id]['message'] = '正在转换音频格式...'

                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                os.system(f"ffmpeg -i {audio_path} {temp_audio.name}")
                audio_path = temp_audio.name

        elif allowed_file(file_info, ALLOWED_VIDEO_EXTENSIONS):
            # 处理视频文件
            processing_tasks[task_id]['progress'] = 10
            processing_tasks[task_id]['message'] = '正在处理视频文件...'

            video_path = os.path.join(UPLOAD_FOLDER, file_info)

            # 提取音频
            processing_tasks[task_id]['progress'] = 15
            processing_tasks[task_id]['message'] = '正在从视频中提取音频...'

            audio_path = extract_audio_from_video(video_path)
        else:
            processing_tasks[task_id]['status'] = 'error'
            processing_tasks[task_id]['message'] = '不支持的文件类型'
            return jsonify({"error": "不支持的文件类型"}), 400

        # 转录音频
        processing_tasks[task_id]['progress'] = 30
        processing_tasks[task_id]['message'] = '正在进行语音识别...'
        text = transcribe_audio(audio_path)

        # 生成摘要
        processing_tasks[task_id]['progress'] = 70
        processing_tasks[task_id]['message'] = '正在生成内容摘要...'
        summary = summarize_with_deepseek(text)

        # 生成关键词和框架
        processing_tasks[task_id]['progress'] = 85
        processing_tasks[task_id]['message'] = '正在提取关键词和分析框架...'
        keywords_and_framework = generate_keywords_and_framework(text, summary)

        # 生成测试问题
        processing_tasks[task_id]['progress'] = 95
        processing_tasks[task_id]['message'] = '正在生成测试问题...'
        test_questions = generate_test_questions(text, summary, keywords_and_framework)

        # 保存到数据库
        processing_tasks[task_id]['progress'] = 98
        processing_tasks[task_id]['message'] = '正在保存处理结果...'

        user_id = session.get('user_id')
        success, history_id = save_usage_history(
            user_id,
            file_info,
            text,
            summary,
            keywords_and_framework,
            test_questions
        )

        # 处理完成
        processing_tasks[task_id]['status'] = 'completed'
        processing_tasks[task_id]['progress'] = 100
        processing_tasks[task_id]['message'] = '处理完成'

        return jsonify({
            "original_text": text,
            "summary": summary,
            "keywords_and_framework": keywords_and_framework,
            "test_questions": test_questions,
            "history_id": history_id
        })

    except Exception as e:
        processing_tasks[task_id]['status'] = 'error'
        processing_tasks[task_id]['message'] = f'处理出错: {str(e)}'
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
