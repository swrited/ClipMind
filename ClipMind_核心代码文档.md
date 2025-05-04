# ClipMind 核心代码文档

## 项目结构

ClipMind项目采用Flask框架构建，主要包含以下核心文件和目录：

```
/root/try/note/
├── audio_video_summarizer.py  # 主应用程序文件
├── run_app.py                 # 应用启动文件
├── schema.sql                 # 数据库模式定义
├── static/                    # 静态资源文件
├── templates/                 # HTML模板文件
│   ├── home_new.html          # 首页模板
│   ├── index_new.html         # 主功能页模板
│   ├── profile.html           # 个人中心页模板
│   ├── history_detail.html    # 历史记录详情页模板
│   ├── login_new.html         # 登录页模板
│   └── register_new.html      # 注册页模板
├── uploads/                   # 上传文件存储目录
└── users.db                   # SQLite数据库文件
```

## 核心模块介绍

### 1. 语音识别模块

语音识别模块支持多种服务，包括科大讯飞、Whisper、Vosk等，实现了音视频内容的文字转换。

```python
def transcribe_audio(audio_path):
    """Convert audio to text using speech recognition"""
    
    # 根据配置选择语音识别服务
    if SPEECH_RECOGNITION_SERVICE == "xunfei_official" and XUNFEI_OFFICIAL_AVAILABLE:
        print("使用科大讯飞官方WebSocket语音识别服务")
        return transcribe_with_xunfei_official(audio_path)
    elif SPEECH_RECOGNITION_SERVICE == "whisper_cli" and WHISPER_CLI_AVAILABLE:
        print("使用Whisper CLI语音识别服务")
        return transcribe_with_whisper_cli(audio_path, model_size="tiny", language="zh", to_simplified=True)
    # 其他语音识别服务选项...
```

### 2. AI内容分析模块

使用DeepSeek API进行内容分析，包括摘要生成、关键词提取和测试问题生成。

```python
def summarize_with_deepseek(text):
    """Use DeepSeek API to summarize the text"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的内容总结助手。请对以下内容进行简洁、全面的总结归纳，提取关键信息和主要观点。"},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
    result = response.json()
    return result["choices"][0]["message"]["content"]
```

### 3. 数据库模块

使用SQLite数据库存储用户信息、使用历史和对话记录。

```python
# 数据库表结构
"""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usage_history_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usage_history_id) REFERENCES usage_history(id)
);
"""

# 保存使用历史示例
def save_usage_history(user_id, filename, original_text, summary, keywords_and_framework, test_questions):
    """保存使用历史到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO usage_history 
    (user_id, filename, original_text, summary, keywords_and_framework, test_questions) 
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, filename, original_text, summary, keywords_and_framework, test_questions))
    conn.commit()
    history_id = cursor.lastrowid
    conn.close()
    return history_id
```

### 4. 文件处理模块

处理上传的音视频文件，包括文件验证、音频提取和临时文件管理。

```python
def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file"""
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(temp_audio.name, codec='pcm_s16le')
    return temp_audio.name

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
```

### 5. 用户认证模块

实现用户注册、登录和会话管理功能。

```python
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
```

### 6. 前端交互模块

使用JavaScript实现前端交互，包括文件上传、进度显示和聊天功能。

```javascript
// 文件上传和处理
submitBtn.addEventListener('click', function() {
    if (!fileUpload.files || !fileUpload.files[0]) {
        return;
    }

    const file = fileUpload.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // 显示进度条
    progressContainer.style.display = 'block';
    progressBarFill.style.width = '0%';
    progressText.textContent = '准备中...';

    // 上传文件并获取任务ID
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const taskId = data.task_id;
        
        // 启动进度轮询
        const progressInterval = pollProgress(taskId);
        
        // 开始处理任务
        return fetch(`/process/${taskId}?file=${encodeURIComponent(file.name)}`)
            .finally(() => {
                clearInterval(progressInterval);
            });
    })
    .then(response => response.json())
    .then(data => {
        // 处理结果
        rawData.original_text = data.original_text;
        rawData.summary = data.summary;
        rawData.keywords_and_framework = data.keywords_and_framework || '';
        rawData.test_questions = data.test_questions || '';
        rawData.history_id = data.history_id || null;
        
        // 显示结果
        displayResults();
    });
});
```

### 7. 聊天功能模块

实现与AI助教的对话功能，并保存对话历史。

```python
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data['message']
    context = data['context']
    history_id = context.get('history_id', None)
    chat_history = data.get('chat_history', [])

    # 构建提示词
    prompt = f"""
    你是一个教育助手，正在与用户进行关于以下内容的对话。
    你的任务是帮助用户理解内容，回答他们的问题，并测试他们的理解。

    原文内容：{context.get('original_text', '')}
    内容摘要：{context.get('summary', '')}
    测试问题：{context.get('test_questions', '')}
    """

    # 调用AI API获取回复
    response = call_ai_api(prompt, user_message, chat_history)
    
    # 保存对话记录
    if history_id:
        save_chat_message(history_id, 'user', user_message)
        save_chat_message(history_id, 'assistant', response)

    return jsonify({"response": response})
```

## 关键技术实现

### 1. 异步任务处理与进度跟踪

实现了任务进度跟踪机制，使用户能够实时了解处理进度。

```python
# 处理进度跟踪
processing_tasks = {}  # 格式: {task_id: {'status': '状态', 'progress': 百分比, 'message': '消息'}}

@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    if task_id in processing_tasks:
        return jsonify(processing_tasks[task_id])
    return jsonify({'status': 'unknown', 'progress': 0, 'message': '任务不存在'})

# 前端轮询进度
function pollProgress(taskId) {
    const pollInterval = setInterval(() => {
        fetch(`/progress/${taskId}`)
            .then(response => response.json())
            .then(data => {
                // 更新进度条
                progressBarFill.style.width = `${data.progress}%`;
                progressText.textContent = data.message;
            });
    }, 1000); // 每秒轮询一次
    
    return pollInterval;
}
```

### 2. 多标签页内容导航

使用标签页组织不同类型的内容，提升用户体验。

```javascript
// 绑定导航菜单事件
const navButtons = document.querySelectorAll('.nav-btn');
navButtons.forEach(button => {
    button.addEventListener('click', function() {
        // 移除所有按钮的active类
        navButtons.forEach(btn => btn.classList.remove('active'));
        // 给当前点击的按钮添加active类
        this.classList.add('active');

        // 隐藏所有内容区域
        const contentSections = document.querySelectorAll('.content-section');
        contentSections.forEach(section => section.classList.remove('active'));

        // 显示对应的内容区域
        const targetId = this.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    });
});
```

### 3. 历史记录与对话连续性

实现了历史记录保存和恢复功能，支持用户随时回顾和继续之前的对话。

```html
<!-- 历史记录详情页中的聊天功能 -->
<div class="chat-container" id="chatContainer">
  {% if chat_history %}
    {% for message in chat_history %}
      <div class="chat-message {% if message.role == 'user' %}user-message{% else %}assistant-message{% endif %}">
        <div class="message-content">{{ message.content }}</div>
        <div class="message-time">{{ message.created_at }}</div>
      </div>
    {% endfor %}
  {% else %}
    <div class="text-center text-muted">
      <p>暂无对话记录，开始提问吧！</p>
    </div>
  {% endif %}
</div>
```

## 前端设计

### 1. 响应式布局

使用Bootstrap框架实现响应式设计，适配不同设备屏幕。

```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}" type="text/css" media="all" />
```

### 2. 动画效果

添加了适当的动画效果，提升用户体验。

```css
/* 图片动画效果 */
.hero-image {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
  100% {
    transform: translateY(0px);
  }
}
```

### 3. 主题设计

采用蓝色为主色调，搭配白色背景，营造专业、清新的视觉效果。

```css
:root {
  --primary-color: #4fc1f0;
  --secondary-color: #151948;
  --light-color: #f8f9fa;
  --dark-color: #333;
}

.hero-title {
  color: var(--secondary-color);
}

.cta-btn {
  background-color: var(--primary-color);
  color: white;
}
```

## 安全性考虑

### 1. 用户认证

使用密码哈希保护用户密码安全。

```python
def create_user(username, password):
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hashed_password))
```

### 2. 输入验证

对用户输入进行验证，防止恶意输入。

```python
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

if not allowed_file(file_info, ALLOWED_AUDIO_EXTENSIONS) and not allowed_file(file_info, ALLOWED_VIDEO_EXTENSIONS):
    return jsonify({"error": "不支持的文件类型"}), 400
```

### 3. 会话管理

使用Flask会话管理用户登录状态。

```python
# 设置密钥用于会话
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_development')

# 检查用户是否登录
if 'user_id' not in session:
    return redirect(url_for('login'))
```

## 总结

ClipMind项目的核心代码实现了从音视频内容提取到AI分析，再到用户交互的完整流程。通过模块化设计和现代Web技术，提供了流畅的用户体验和强大的功能。项目代码结构清晰，易于维护和扩展，为未来功能迭代奠定了良好基础。
