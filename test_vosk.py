import os
import tempfile
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file"""
    print(f"从视频中提取音频: {video_path}")
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(temp_audio.name, codec='pcm_s16le')
    print(f"音频已保存到: {temp_audio.name}")
    return temp_audio.name

def main():
    # 视频文件路径
    video_path = "/root/try/test/7分阅读6-4.mp4"
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return
    
    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)
    
    # 使用 audio_video_summarizer.py 中的 transcribe_audio 函数
    from audio_video_summarizer import transcribe_audio
    result = transcribe_audio(audio_path)
    
    # 打印结果
    print("\n=== 识别结果 ===")
    print(result)

if __name__ == "__main__":
    main()
