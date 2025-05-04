"""
科大讯飞语音识别模块

这个模块提供了使用科大讯飞语音识别 API 进行语音转文字的功能。
"""

import os
import time
import json
import hashlib
import base64
import hmac
import requests
import urllib.parse
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 科大讯飞语音识别 API 配置
XUNFEI_APP_ID = os.getenv("XUNFEI_APP_ID", "")
XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY", "")
XUNFEI_API_SECRET = os.getenv("XUNFEI_API_SECRET", "")

# 科大讯飞语音识别 API 地址
API_URL = "https://iat-api.xfyun.cn/v2/iat"

def generate_signature(host, date, method, api_key, api_secret, path):
    """
    生成科大讯飞 API 签名
    """
    # 拼接字符串
    signature_origin = "host: " + host + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += method + " " + path + " HTTP/1.1"

    # 检查 api_secret 是否已经是 Base64 编码
    try:
        # 尝试解码 api_secret
        decoded_secret = base64.b64decode(api_secret)
        # 如果成功解码，使用解码后的值
        api_secret_bytes = decoded_secret
    except:
        # 如果解码失败，直接使用原始值
        api_secret_bytes = api_secret.encode('utf-8')

    # 进行hmac-sha256进行加密
    signature_sha = hmac.new(api_secret_bytes, signature_origin.encode('utf-8'),
                           digestmod=hashlib.sha256).digest()

    # 进行base64编码
    signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

    # 进行base64编码
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

    return authorization

def transcribe_with_xunfei(audio_path, language='cn'):
    """
    使用科大讯飞语音识别服务进行语音识别

    参数:
        audio_path (str): 音频文件路径
        language (str): 语言代码，默认为中文

    返回:
        str: 识别的文本
    """
    print(f"\n\n=== 开始科大讯飞语音识别 ===")
    print(f"音频文件路径: {audio_path}")

    if not all([XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET]):
        return "未配置科大讯飞语音识别 API 密钥。请在 .env 文件中设置 XUNFEI_APP_ID, XUNFEI_API_KEY 和 XUNFEI_API_SECRET。"

    try:
        # 打印 API 密钥信息（仅用于调试）
        print(f"科大讯飞 API 配置:")
        print(f"APP_ID: {XUNFEI_APP_ID}")
        print(f"API_KEY: {XUNFEI_API_KEY}")
        print(f"API_SECRET: {XUNFEI_API_SECRET}")

        # 读取音频文件
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        # 将音频数据进行base64编码
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # 构建请求参数
        url = API_URL
        host = "iat-api.xfyun.cn"
        path = "/v2/iat"
        method = "POST"

        # 获取当前时间并格式化
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 生成签名
        authorization = generate_signature(host, date, method, XUNFEI_API_KEY, XUNFEI_API_SECRET, path)
        print(f"生成的签名: {authorization}")

        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": host,
            "Date": date,
            "Authorization": authorization
        }
        print(f"请求头: {headers}")

        # 设置请求参数
        data = {
            "common": {
                "app_id": XUNFEI_APP_ID
            },
            "business": {
                "language": language,  # 语种, 中文=cn, 英文=en, 日语=ja, 韩语=ko
                "domain": "iat",       # 领域, iat=日常用语
                "accent": "mandarin",  # 方言, mandarin=普通话
                "vad_eos": 3000        # 静默检测（end of speech），静默时长超过该值停止音频流识别
            },
            "data": {
                "status": 2,           # 2: 最后一帧音频
                "format": "audio/wav", # 音频格式
                "encoding": "raw",     # 音频编码, raw=原生音频数据
                "audio": audio_base64  # base64编码后的音频数据
            }
        }

        # 发送请求
        print(f"发送请求到: {url}")
        print(f"请求数据: {json.dumps(data, indent=2)}")
        response = requests.post(url, json=data, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        response.raise_for_status()
        result = response.json()

        # 解析结果
        if result["code"] == 0:
            # 识别成功
            text = ""
            for item in result["data"]["result"]["ws"]:
                for w in item["cw"]:
                    text += w["w"]
            return text
        else:
            # 识别失败
            return f"科大讯飞语音识别失败: {result['code']} - {result.get('message', '未知错误')}"

    except Exception as e:
        print(f"调用科大讯飞语音识别 API 时出错: {e}")
        return f"调用科大讯飞语音识别 API 时出错: {e}"
