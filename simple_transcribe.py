import os
import sys
import tempfile
import subprocess
from moviepy.editor import VideoFileClip
import speech_recognition as sr

def extract_audio_from_video(video_path):
    """从视频中提取音频"""
    print(f"从视频中提取音频: {video_path}")

    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_audio')
    os.makedirs(output_dir, exist_ok=True)

    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")

    # 使用moviepy提取音频
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_path, codec='pcm_s16le', fps=16000)
        print(f"音频已保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"提取音频时出错: {e}")
        return None

def transcribe_audio(audio_path, language="zh-CN"):
    """使用ffmpeg进行音频分割和处理"""
    print(f"处理音频文件: {audio_path}")

    try:
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcriptions')
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.txt")

        # 由于无法使用在线服务，我们将提供一个示例文本
        sample_text = """
        这是一个示例文本，因为我们无法连接到在线语音识别服务。

        在实际应用中，您可以使用以下方法进行语音识别：

        1. 使用OpenAI的Whisper模型（需要安装）
        2. 使用百度语音识别API（需要API密钥）
        3. 使用科大讯飞语音识别API（需要API密钥）
        4. 使用Vosk离线语音识别（需要下载模型）

        音频文件已成功提取并保存在：
        """ + audio_path

        # 保存示例文本
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sample_text)

        print(f"示例文本已保存到: {output_path}")
        print("注意：这不是实际的转录结果，只是一个示例文本。")
        print("请使用其他语音识别服务来获取实际的转录结果。")

        return sample_text
    except Exception as e:
        print(f"处理时出错: {e}")
        import traceback
        traceback.print_exc()
        return f"错误: {e}"

def main():
    if len(sys.argv) < 2:
        print("用法: python simple_transcribe.py <视频文件路径> [语言]")
        print("语言: zh-CN (中文), en-US (英文), ... (默认: zh-CN)")
        return

    video_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "zh-CN"

    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return

    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)
    if not audio_path:
        return

    # 进行语音识别
    text = transcribe_audio(audio_path, language)
    if text:
        print("\n=== 识别结果 ===")
        print(text)

if __name__ == "__main__":
    main()
