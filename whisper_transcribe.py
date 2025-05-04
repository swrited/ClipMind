import os
import sys
import tempfile
import time
from moviepy.editor import VideoFileClip
from opencc import OpenCC

def extract_audio_from_video(video_path):
    """从视频中提取音频"""
    print(f"从视频中提取音频: {video_path}")

    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_audio')
    os.makedirs(output_dir, exist_ok=True)

    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")

    # 如果音频文件已存在，直接返回路径
    if os.path.exists(output_path):
        print(f"音频文件已存在: {output_path}")
        return output_path

    # 使用moviepy提取音频
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_path, codec='pcm_s16le', fps=16000)
        print(f"音频已保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"提取音频时出错: {e}")
        return None

def transcribe_with_whisper(audio_path, model_size="small", language="Chinese", to_simplified=True):
    """使用Whisper进行语音识别"""
    print(f"使用Whisper进行语音识别: {audio_path}")
    print(f"模型大小: {model_size}, 语言: {language}, 转换为简体: {to_simplified}")

    try:
        import whisper

        # 加载模型
        print("加载Whisper模型...")
        start_time = time.time()
        model = whisper.load_model(model_size)
        load_time = time.time() - start_time
        print(f"模型加载完成，耗时: {load_time:.2f} 秒")

        # 进行转录
        print("开始转录...")
        start_time = time.time()
        result = model.transcribe(audio_path, language=language, verbose=True)
        transcribe_time = time.time() - start_time
        print(f"转录完成，耗时: {transcribe_time:.2f} 秒")

        # 获取转录文本
        text = result["text"]

        # 如果需要，将繁体中文转换为简体中文
        if to_simplified and language.lower() in ["chinese", "zh", "zh-cn", "zh-tw"]:
            print("将繁体中文转换为简体中文...")
            cc = OpenCC('t2s')  # 繁体到简体
            text = cc.convert(text)
            print("转换完成")

        # 保存结果
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcriptions')
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_whisper.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"转录结果已保存到: {output_path}")
        return text
    except Exception as e:
        print(f"转录时出错: {e}")
        import traceback
        traceback.print_exc()
        return f"Whisper语音识别出错: {e}"

def main():
    if len(sys.argv) < 2:
        print("用法: python whisper_transcribe.py <视频文件路径> [模型大小] [语言] [是否转换为简体]")
        print("模型大小: tiny, base, small, medium, large (默认: small)")
        print("语言: Chinese, English, Japanese, ... (默认: Chinese)")
        print("是否转换为简体: true, false (默认: true)")
        return

    video_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "small"
    language = sys.argv[3] if len(sys.argv) > 3 else "Chinese"
    to_simplified = sys.argv[4].lower() != "false" if len(sys.argv) > 4 else True

    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return

    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)
    if not audio_path:
        return

    # 使用Whisper进行语音识别
    text = transcribe_with_whisper(audio_path, model_size, language, to_simplified)
    if text:
        print("\n=== 识别结果 ===")
        print(text)

if __name__ == "__main__":
    main()
