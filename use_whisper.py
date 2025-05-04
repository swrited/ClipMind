#!/usr/bin/env python3
"""
使用Whisper进行语音识别的简单脚本
"""

import os
import sys
import time
import subprocess
from moviepy.editor import VideoFileClip

def extract_audio(video_path):
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

def run_whisper_cli(audio_path, model_size="tiny", language="zh"):
    """使用Whisper CLI工具进行语音识别"""
    print(f"使用Whisper CLI进行语音识别: {audio_path}")
    print(f"模型大小: {model_size}, 语言: {language}")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcriptions')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_whisper_cli.txt")
    
    # 构建Whisper CLI命令
    cmd = f"whisper {audio_path} --model {model_size} --language {language} --output_dir {output_dir}"
    print(f"执行命令: {cmd}")
    
    # 执行命令
    try:
        start_time = time.time()
        subprocess.run(cmd, shell=True, check=True)
        end_time = time.time()
        print(f"转录完成，耗时: {end_time - start_time:.2f} 秒")
        
        # Whisper CLI输出的文本文件与输入文件同名，但扩展名为.txt
        whisper_output = os.path.join(output_dir, f"{base_name}.txt")
        
        # 如果输出文件存在，读取内容并保存到我们的输出文件
        if os.path.exists(whisper_output):
            with open(whisper_output, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 保存到我们的输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"转录结果已保存到: {output_path}")
            return text
        else:
            print(f"无法找到Whisper输出文件: {whisper_output}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"执行Whisper CLI时出错: {e}")
        return None
    except Exception as e:
        print(f"转录时出错: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("用法: python use_whisper.py <视频文件路径> [模型大小] [语言]")
        print("模型大小: tiny, base, small, medium, large (默认: tiny)")
        print("语言: zh, en, ja, ... (默认: zh)")
        return
    
    video_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "tiny"
    language = sys.argv[3] if len(sys.argv) > 3 else "zh"
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 文件不存在: {video_path}")
        return
    
    # 从视频中提取音频
    audio_path = extract_audio(video_path)
    if not audio_path:
        return
    
    # 使用Whisper CLI进行语音识别
    text = run_whisper_cli(audio_path, model_size, language)
    if text:
        print("\n=== 识别结果 ===")
        print(text)

if __name__ == "__main__":
    main()
