import os
import sys
import time
import tempfile
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 获取OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

def transcribe_with_openai(audio_path, model="whisper-1", language="zh"):
    """使用OpenAI API进行语音识别"""
    print(f"使用OpenAI API进行语音识别: {audio_path}")
    print(f"模型: {model}, 语言: {language}")
    
    if not OPENAI_API_KEY:
        print("错误: 未设置OPENAI_API_KEY环境变量")
        return "未设置OPENAI_API_KEY环境变量。请在.env文件中设置OPENAI_API_KEY。"
    
    try:
        # 初始化OpenAI客户端
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 打开音频文件
        with open(audio_path, "rb") as audio_file:
            # 发送请求
            print("发送请求到OpenAI API...")
            start_time = time.time()
            
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
                response_format="text"
            )
            
            end_time = time.time()
            print(f"请求完成，耗时: {end_time - start_time:.2f} 秒")
            
            # 保存结果
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcriptions')
            os.makedirs(output_dir, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_openai.txt")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response)
            
            print(f"转录结果已保存到: {output_path}")
            return response
    except Exception as e:
        print(f"转录时出错: {e}")
        import traceback
        traceback.print_exc()
        return f"错误: {e}"

def main():
    if len(sys.argv) < 2:
        print("用法: python openai_transcribe.py <视频文件路径> [语言]")
        print("语言: zh (中文), en (英文), ... (默认: zh)")
        return
    
    video_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "zh"
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return
    
    # 从视频中提取音频
    audio_path = extract_audio_from_video(video_path)
    if not audio_path:
        return
    
    # 使用OpenAI API进行语音识别
    text = transcribe_with_openai(audio_path, language=language)
    if text:
        print("\n=== 识别结果 ===")
        print(text)

if __name__ == "__main__":
    main()
