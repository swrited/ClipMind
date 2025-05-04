import base64
import hashlib
import hmac
import json
import os
import time
import urllib
import urllib.request
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 科大讯飞语音识别 API 配置
XUNFEI_APP_ID = os.getenv("XUNFEI_APP_ID", "")
XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY", "")
XUNFEI_API_SECRET = os.getenv("XUNFEI_API_SECRET", "")

# 打印配置信息
print(f"APP_ID: {XUNFEI_APP_ID}")
print(f"API_KEY: {XUNFEI_API_KEY}")
print(f"API_SECRET: {XUNFEI_API_SECRET}")

# 读取音频文件
audio_path = "/tmp/tmpbiqle4ei.wav"  # 使用之前提取的音频文件
with open(audio_path, 'rb') as f:
    audio_data = f.read()

# 将音频数据进行base64编码
audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# 构建请求参数
url = "https://iat-api.xfyun.cn/v2/iat"
host = "iat-api.xfyun.cn"
path = "/v2/iat"
method = "POST"

# 获取当前时间并格式化
now = datetime.now()
date = format_date_time(mktime(now.timetuple()))

# 拼接字符串
signature_origin = "host: " + host + "\n"
signature_origin += "date: " + date + "\n"
signature_origin += method + " " + path + " HTTP/1.1"

# 进行hmac-sha256进行加密
signature_sha = hmac.new(XUNFEI_API_SECRET.encode('utf-8'), signature_origin.encode('utf-8'),
                       digestmod=hashlib.sha256).digest()

# 进行base64编码
signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

authorization_origin = f'api_key="{XUNFEI_API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

# 进行base64编码
authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

# 设置请求头
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Host": host,
    "Date": date,
    "Authorization": authorization
}

# 设置请求参数
data = {
    "common": {
        "app_id": XUNFEI_APP_ID
    },
    "business": {
        "language": "cn",  # 语种, 中文=cn, 英文=en, 日语=ja, 韩语=ko
        "domain": "iat",   # 领域, iat=日常用语
        "accent": "mandarin",  # 方言, mandarin=普通话
        "vad_eos": 3000    # 静默检测（end of speech），静默时长超过该值停止音频流识别
    },
    "data": {
        "status": 2,       # 2: 最后一帧音频
        "format": "audio/wav", # 音频格式
        "encoding": "raw",  # 音频编码, raw=原生音频数据
        "audio": audio_base64  # base64编码后的音频数据
    }
}

# 发送请求
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode('utf-8'))
    print("识别结果:")
    print(json.dumps(result, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(f"请求失败: {e.code} {e.reason}")
    print(e.read().decode('utf-8'))
