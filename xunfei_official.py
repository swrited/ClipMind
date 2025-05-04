"""
科大讯飞WebSocket语音识别模块 - 官方示例代码

这个模块提供了使用科大讯飞WebSocket API进行语音转文字的功能，基于官方示例代码。
"""

import os
import time
import json
import base64
import hashlib
import hmac
import websocket
from urllib.parse import urlencode
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 科大讯飞语音识别 API 配置
APPID = os.getenv("XUNFEI_APP_ID", "")
API_KEY = os.getenv("XUNFEI_API_KEY", "")
API_SECRET = os.getenv("XUNFEI_API_SECRET", "")

# 科大讯飞WebSocket API地址
API_URL = "wss://iat-api.xfyun.cn/v2/iat"

class XunfeiOfficialRecognizer:
    def __init__(self):
        self.result = ""
        self.ws = None
        self.audio_data = None
        self.status = 0  # 0: 初始化, 1: 连接成功, 2: 识别完成, -1: 错误
        self.error_msg = ""
        self.all_results = []  # 存储所有的识别结果

    def create_url(self):
        """
        生成WebSocket URL
        """
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        host = "iat-api.xfyun.cn"
        signature_origin = f"host: {host}\ndate: {date}\nGET /v2/iat HTTP/1.1"
        
        # 进行hmac-sha256加密
        print(f"APPID: {APPID}")
        print(f"API Key: {API_KEY[:10]}...")
        print(f"API Secret: {API_SECRET[:10]}...")
        print(f"签名原文: {signature_origin}")
        
        signature_sha = hmac.new(API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'),
                              digestmod=hashlib.sha256).digest()
        
        # 进行base64编码
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        
        # 进行base64编码
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 构建URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        url = API_URL + '?' + urlencode(v)
        return url

    def on_message(self, ws, message):
        """
        接收消息回调
        """
        try:
            print(f"收到消息: {message[:100]}...")
            message = json.loads(message)
            if message["code"] != 0:
                self.status = -1
                self.error_msg = f"识别失败: {message['code']} - {message.get('message', '未知错误')}"
                print(f"识别失败: {self.error_msg}")
                ws.close()
                return

            # 检查是否有结果
            if "data" in message and "result" in message["data"]:
                if "ws" in message["data"]["result"]:
                    data = message["data"]["result"]["ws"]
                    result = ""
                    for i in data:
                        for w in i["cw"]:
                            result += w["w"]

                    print(f"识别结果片段: {result}")
                    self.all_results.append(result)
                    self.result += result

            # 检查是否是最后一帧
            if "data" in message and "status" in message["data"] and message["data"]["status"] == 2:
                print("识别完成")
                self.status = 2
                ws.close()
        except Exception as e:
            self.status = -1
            self.error_msg = f"处理消息时出错: {str(e)}"
            print(f"处理消息时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            ws.close()

    def on_error(self, ws, error):
        """
        错误回调
        """
        self.status = -1
        self.error_msg = f"WebSocket错误: {str(error)}"
        print(f"WebSocket错误: {str(error)}")
        ws.close()

    def on_close(self, ws, close_status_code, close_msg):
        """
        关闭回调
        """
        print(f"WebSocket连接关闭: {close_status_code}, {close_msg}")
        if self.status != 2 and self.status != -1:
            self.status = -1
            self.error_msg = f"WebSocket连接关闭: {close_status_code}, {close_msg}"

    def on_open(self, ws):
        """
        连接建立回调
        """
        self.status = 1
        print("WebSocket连接已建立，开始发送数据...")

        def send_data():
            """
            发送数据
            """
            try:
                # 发送开始帧
                frame_size = 8000  # 每一帧的大小
                intervel = 0.04  # 发送间隔(单位:s)
                status = 0  # 音频的状态: 0-第一帧, 1-中间帧, 2-最后一帧

                audio_len = len(self.audio_data)
                print(f"音频总长度: {audio_len} 字节")

                # 发送第一帧
                if audio_len <= frame_size:
                    # 音频长度小于一帧，直接发送完整音频
                    first_frame = self.audio_data
                    status = 2  # 最后一帧
                else:
                    # 发送第一帧
                    first_frame = self.audio_data[:frame_size]

                data = {
                    "common": {
                        "app_id": APPID
                    },
                    "business": {
                        "language": "zh_cn",  # 语种, 中文=zh_cn, 英文=en_us
                        "domain": "iat",      # 领域, iat=日常用语
                        "accent": "mandarin", # 方言, mandarin=普通话
                        "vad_eos": 10000,     # 静默检测（end of speech），静默时长超过该值停止音频流识别
                        "dwa": "wpgs",        # 动态修正功能
                        "pd": "game"          # 领域个性化参数：game表示游戏
                    },
                    "data": {
                        "status": status,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": base64.b64encode(first_frame).decode('utf-8')
                    }
                }
                ws.send(json.dumps(data))
                print(f"已发送第一帧数据: {len(first_frame)} 字节, 状态: {status}")

                # 如果音频长度大于一帧，继续发送后续帧
                if audio_len > frame_size:
                    total_frames = int((audio_len - 1) / frame_size) + 1
                    print(f"总帧数: {total_frames}")

                    for i in range(1, total_frames):
                        start = i * frame_size
                        end = min(start + frame_size, audio_len)
                        frame = self.audio_data[start:end]

                        # 最后一帧
                        if end == audio_len:
                            status = 2
                        else:
                            status = 1

                        data = {
                            "data": {
                                "status": status,
                                "format": "audio/L16;rate=16000",
                                "encoding": "raw",
                                "audio": base64.b64encode(frame).decode('utf-8')
                            }
                        }
                        ws.send(json.dumps(data))
                        print(f"已发送第 {i+1}/{total_frames} 帧数据: {len(frame)} 字节, 状态: {status}")
                        time.sleep(intervel)

                print("所有数据已发送完毕")
            except Exception as e:
                self.status = -1
                self.error_msg = f"发送数据时出错: {str(e)}"
                print(f"发送数据时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                ws.close()

        import threading
        threading.Thread(target=send_data).start()

    def recognize(self, audio_data):
        """
        识别音频

        参数:
            audio_data (bytes): 音频数据

        返回:
            str: 识别的文本
        """
        self.audio_data = audio_data
        self.result = ""
        self.all_results = []
        self.status = 0
        self.error_msg = ""

        # 创建WebSocket连接
        url = self.create_url()
        print(f"WebSocket URL: {url}")
        websocket.enableTrace(True)  # 启用跟踪以便调试
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        # 启动WebSocket连接
        print("启动WebSocket连接...")
        self.ws.run_forever()

        # 等待识别完成或出错
        if self.status == 2:
            print(f"识别完成，共获取 {len(self.all_results)} 个结果片段")
            return self.result
        else:
            print(f"识别失败: {self.error_msg}")
            return self.error_msg

def transcribe_with_xunfei_official(audio_path, language='zh_cn'):
    """
    使用科大讯飞WebSocket API进行语音识别

    参数:
        audio_path (str): 音频文件路径
        language (str): 语言代码，默认为中文

    返回:
        str: 识别的文本
    """
    print(f"\n\n=== 开始科大讯飞WebSocket语音识别（官方版本）===")
    print(f"音频文件路径: {audio_path}")

    if not all([APPID, API_KEY, API_SECRET]):
        return "未配置科大讯飞语音识别 API 密钥。请在 .env 文件中设置 XUNFEI_APP_ID, XUNFEI_API_KEY 和 XUNFEI_API_SECRET。"

    try:
        # 检查音频格式，如果不是16kHz的WAV，则进行转换
        import wave
        try:
            with wave.open(audio_path, 'rb') as wf:
                if wf.getframerate() != 16000 or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    print(f"音频格式不符合要求，需要转换")
                    import tempfile
                    import os
                    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    temp_wav.close()
                    os.system(f"ffmpeg -i {audio_path} -ar 16000 -ac 1 -acodec pcm_s16le {temp_wav.name}")
                    audio_path = temp_wav.name
                    print(f"已转换音频格式，新文件: {audio_path}")
        except Exception as e:
            print(f"检查音频格式时出错: {e}")
            # 尝试强制转换
            import tempfile
            import os
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            os.system(f"ffmpeg -i {audio_path} -ar 16000 -ac 1 -acodec pcm_s16le {temp_wav.name}")
            audio_path = temp_wav.name
            print(f"已强制转换音频格式，新文件: {audio_path}")

        # 读取音频文件
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        print(f"音频数据大小: {len(audio_data)} 字节")

        # 创建识别器
        recognizer = XunfeiOfficialRecognizer()

        # 进行识别
        result = recognizer.recognize(audio_data)

        return result
    except Exception as e:
        print(f"科大讯飞WebSocket语音识别出错: {e}")
        import traceback
        traceback.print_exc()
        return f"科大讯飞WebSocket语音识别出错: {e}"
