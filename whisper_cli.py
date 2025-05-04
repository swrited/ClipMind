"""
Whisper CLI语音识别模块

这个模块提供了使用Whisper CLI工具进行语音转文字的功能。
"""

import os
import subprocess
import time

# 导入繁体转简体的库
try:
    from opencc import OpenCC
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("OpenCC未安装，将不能进行繁体转简体转换")

def transcribe_with_whisper_cli(audio_path, model_size="tiny", language="zh", to_simplified=True):
    """
    使用Whisper CLI工具进行语音识别

    参数:
        audio_path (str): 音频文件路径
        model_size (str): 模型大小，可选值: tiny, base, small, medium, large (默认: tiny)
        language (str): 语言代码，默认为中文
        to_simplified (bool): 是否将繁体中文转换为简体中文，默认为True

    返回:
        str: 识别的文本
    """
    print(f"\n\n=== 开始Whisper CLI语音识别 ===")
    print(f"音频文件路径: {audio_path}")
    print(f"模型大小: {model_size}, 语言: {language}")

    try:
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

            # 如果需要，将繁体中文转换为简体中文
            if to_simplified and language.lower() in ["zh", "chinese", "zh-cn", "zh-tw"] and OPENCC_AVAILABLE:
                print("将繁体中文转换为简体中文...")
                cc = OpenCC('t2s')  # 繁体到简体
                text = cc.convert(text)
                print("转换完成")

            # 保存到我们的输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"转录结果已保存到: {output_path}")
            return text
        else:
            error_msg = f"无法找到Whisper输出文件: {whisper_output}"
            print(error_msg)
            return error_msg
    except subprocess.CalledProcessError as e:
        error_msg = f"执行Whisper CLI时出错: {e}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"转录时出错: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg
