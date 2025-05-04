#!/usr/bin/env python3
"""
启动脚本，用于应用 Werkzeug 补丁并启动应用程序
"""

# 首先应用补丁
import werkzeug_patch

# 然后导入并运行应用程序
from audio_video_summarizer import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
