"""
百度语音识别模块

这个模块提供了使用百度语音识别 API 进行语音转文字的功能。
"""

import os
import json
from aip import AipSpeech
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 百度语音识别 API 配置
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID", "")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")

def transcribe_with_baidu(audio_path, language='zh'):
    """
    使用百度语音识别服务进行语音识别

    参数:
        audio_path (str): 音频文件路径
        language (str): 语言代码，默认为中文

    返回:
        str: 识别的文本
    """
    if not all([BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY]):
        return "未配置百度语音识别 API 密钥。请在 .env 文件中设置 BAIDU_APP_ID, BAIDU_API_KEY 和 BAIDU_SECRET_KEY。"

    # 创建 AipSpeech 客户端
    client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

    # 读取音频文件
    try:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
    except Exception as e:
        return f"读取音频文件失败: {e}"

    # 设置语音识别参数
    options = {
        'dev_pid': 1537,  # 普通话(支持简单的英文识别)
        'format': 'wav',  # 音频格式
        'rate': 16000,    # 采样率
        'channel': 1,     # 声道数
    }

    # 发送请求
    try:
        result = client.asr(audio_data, options.get('format'), options.get('rate'), options)

        if result.get("err_no") == 0:
            # 识别成功
            return result.get("result")[0]
        else:
            # 识别失败
            error_msg = result.get('err_msg', '未知错误')
            print(f"百度语音识别失败: {error_msg}")
            return f"百度语音识别失败: {error_msg}"
    except Exception as e:
        print(f"调用百度语音识别 API 时出错: {e}")
        return f"调用百度语音识别 API 时出错: {e}"
