"""
Vosk 语音识别模块

这个模块提供了使用 Vosk 进行离线语音识别的功能。
"""

import os
import json
import wave
from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Vosk 模型路径
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "vosk-model-cn")

def transcribe_with_vosk(audio_path, language='zh'):
    """
    使用 Vosk 进行离线语音识别
    
    参数:
        audio_path (str): 音频文件路径
        language (str): 语言代码，默认为中文
        
    返回:
        str: 识别的文本
    """
    # 检查模型是否存在
    if not os.path.exists(VOSK_MODEL_PATH):
        return f"Vosk 模型不存在。请下载模型并将其放在 {VOSK_MODEL_PATH} 目录中。"
    
    try:
        # 加载模型
        model = Model(VOSK_MODEL_PATH)
        
        # 打开音频文件
        wf = wave.open(audio_path, "rb")
        
        # 检查音频格式
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            return "音频格式不支持。请使用单声道、16位PCM格式的WAV文件。"
        
        # 创建识别器
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        
        # 读取音频数据并进行识别
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part_result = json.loads(rec.Result())
                if "text" in part_result:
                    results.append(part_result["text"])
        
        # 获取最后的结果
        part_result = json.loads(rec.FinalResult())
        if "text" in part_result:
            results.append(part_result["text"])
        
        # 合并结果
        text = " ".join(results)
        
        if not text.strip():
            return "无法识别音频内容。请确保音频清晰并包含语音。"
        
        return text
        
    except Exception as e:
        print(f"Vosk 语音识别出错: {e}")
        return f"Vosk 语音识别出错: {e}"
