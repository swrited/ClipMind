import os
import subprocess
import tempfile

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as temporary WAV file"""
    print(f"从视频中提取音频: {video_path}")

    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_audio')
    os.makedirs(output_dir, exist_ok=True)

    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")

    # 使用ffmpeg直接转换为16kHz, 单声道, 16位PCM WAV
    cmd = f"ffmpeg -i {video_path} -ar 16000 -ac 1 -acodec pcm_s16le {output_path}"
    print(f"执行命令: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

    print(f"音频已保存到: {output_path}")
    return output_path

def main():
    # 视频文件路径
    video_path = "/root/try/test/7分阅读6-4.mp4"

    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return

    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)

    print(f"\n音频已成功提取到: {audio_path}")
    print("您可以使用这个音频文件进行语音识别测试。")

if __name__ == "__main__":
    main()
