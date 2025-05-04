import numpy as np
from scipy.io import wavfile

# 创建一个简单的正弦波音频
sample_rate = 16000  # 采样率
duration = 3  # 持续时间（秒）
frequency = 440  # 频率（赫兹）

# 生成时间数组
t = np.linspace(0, duration, int(sample_rate * duration), False)

# 生成正弦波
audio_data = np.sin(2 * np.pi * frequency * t) * 32767  # 缩放到16位范围

# 转换为16位整数
audio_data = audio_data.astype(np.int16)

# 保存为WAV文件
output_file = "test_files/test_audio.wav"
wavfile.write(output_file, sample_rate, audio_data)

print(f"已创建测试音频文件: {output_file}")
