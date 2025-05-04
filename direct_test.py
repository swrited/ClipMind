import os
import tempfile
import subprocess
from moviepy.editor import VideoFileClip
import time

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file"""
    print(f"从视频中提取音频: {video_path}")
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio.close()
    
    # 使用ffmpeg直接转换为16kHz, 单声道, 16位PCM WAV
    cmd = f"ffmpeg -i {video_path} -ar 16000 -ac 1 -acodec pcm_s16le {temp_audio.name}"
    print(f"执行命令: {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    
    print(f"音频已保存到: {temp_audio.name}")
    return temp_audio.name

def transcribe_with_whisper(audio_path):
    """使用OpenAI的Whisper模型进行语音识别"""
    print(f"使用Whisper进行语音识别: {audio_path}")
    
    # 使用whisper命令行工具
    output_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    output_file.close()
    
    cmd = f"whisper {audio_path} --language Chinese --model small --output_dir /tmp"
    print(f"执行命令: {cmd}")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        # Whisper输出的文本文件与输入文件同名，但扩展名为.txt
        txt_file = os.path.splitext(os.path.basename(audio_path))[0] + ".txt"
        txt_path = os.path.join("/tmp", txt_file)
        
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text
        else:
            return f"无法找到Whisper输出文件: {txt_path}"
    except subprocess.CalledProcessError as e:
        return f"Whisper处理失败: {str(e)}"
    except Exception as e:
        return f"Whisper处理出错: {str(e)}"

def main():
    # 视频文件路径
    video_path = "/root/try/test/7分阅读6-4.mp4"
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return
    
    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)
    
    # 使用Whisper进行语音识别
    start_time = time.time()
    result = transcribe_with_whisper(audio_path)
    end_time = time.time()
    
    # 打印结果
    print(f"\n=== 识别结果 ===")
    print(result)
    print(f"\n识别耗时: {end_time - start_time:.2f} 秒")
    
    # 保存结果到文件
    with open("transcription_result.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"结果已保存到: transcription_result.txt")

if __name__ == "__main__":
    main()
