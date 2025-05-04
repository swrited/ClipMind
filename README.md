# 音视频转文字与总结工具

这是一个基于Flask的Web应用，允许用户上传音频或视频文件，将其转换为文本，然后使用DeepSeek API进行内容总结。
swrited@hotmail.com

## 功能

- 支持上传多种格式的音频文件（mp3, wav, ogg, m4a）
- 支持上传多种格式的视频文件（mp4, avi, mov, mkv）
- 从视频中提取音频
- 使用Google Speech Recognition API将音频转换为文本
- 使用DeepSeek API对文本内容进行总结归纳
- 用户友好的Web界面

## 安装

1. 克隆或下载此仓库
2. 安装依赖项：

```bash
# 使用默认源安装
pip install -r requirements.txt

# 或使用清华源加速下载（推荐国内用户使用）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果想永久设置pip使用清华源，可以执行：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

3. 安装FFmpeg（用于音频处理）：

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# macOS (使用Homebrew)
brew install ffmpeg
```

4. 在`audio_video_summarizer.py`文件中设置您的DeepSeek API密钥：

```python
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY"  # 替换为您的实际API密钥
```

## 使用方法

1. 启动应用：

```bash
python audio_video_summarizer.py
```

2. 在浏览器中访问：`http://localhost:5000`

3. 上传音频或视频文件，点击"开始处理"按钮

4. 等待处理完成，查看原始文本和总结结果

## 注意事项

- 对于较大的文件，处理可能需要一些时间
- 语音识别的准确性取决于音频质量和语言
- 确保您有足够的磁盘空间用于临时文件存储
- 默认支持中文语音识别，可以在代码中修改为其他语言

## 语音识别服务

本应用程序支持四种语音识别服务：

1. **科大讯飞语音识别**（默认）：中国领先的语音识别服务，对中文支持极佳，有免费额度
2. **Vosk 离线语音识别**：完全免费，离线运行，不需要网络连接
3. **百度语音识别**：适用于中国大陆地区，对中文支持更好，需要 API 密钥
4. **Google 语音识别**：全球可用，但在某些地区可能无法访问

### 配置科大讯飞语音识别

1. 在[科大讯飞开放平台](https://www.xfyun.cn/)注册并创建语音听写应用
2. 获取 AppID、API Key 和 API Secret
3. 在 `.env` 文件中设置以下变量：
   ```
   XUNFEI_APP_ID=your_xunfei_app_id
   XUNFEI_API_KEY=your_xunfei_api_key
   XUNFEI_API_SECRET=your_xunfei_api_secret
   SPEECH_RECOGNITION_SERVICE=xunfei
   ```

### 配置 Vosk 离线语音识别

1. 下载 Vosk 中文模型：
   ```bash
   # 创建模型目录
   mkdir -p vosk-model-cn

   # 下载并解压模型
   wget https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
   unzip vosk-model-cn-0.22.zip -d vosk-model-cn
   ```

2. 在 `.env` 文件中设置：
   ```
   SPEECH_RECOGNITION_SERVICE=vosk
   VOSK_MODEL_PATH=vosk-model-cn
   ```

### 配置百度语音识别

1. 在[百度 AI 开放平台](https://ai.baidu.com/tech/speech)注册并创建语音识别应用
2. 获取 API Key、Secret Key 和 App ID
3. 在 `.env` 文件中设置以下变量：
   ```
   BAIDU_API_KEY=your_baidu_api_key
   BAIDU_SECRET_KEY=your_baidu_secret_key
   BAIDU_APP_ID=your_baidu_app_id
   SPEECH_RECOGNITION_SERVICE=baidu
   ```

### 切换到 Google 语音识别

如果您想使用 Google 语音识别服务，请在 `.env` 文件中设置：
```
SPEECH_RECOGNITION_SERVICE=google
```

## 故障排除

### 语音识别问题

如果遇到"无法连接到语音识别服务"的错误，可能是由以下原因导致的：

1. **网络连接问题**：确保您的服务器可以访问互联网，特别是 Google 的服务
2. **防火墙限制**：检查是否有防火墙阻止了对 Google API 的访问
3. **区域限制**：某些地区可能无法访问 Google 的服务，可以考虑使用 VPN
4. **API 限制**：Google 的免费语音识别 API 有使用限制，可能需要等待一段时间再试

解决方案：
- 检查网络连接
- 尝试使用不同的音频文件
- 应用程序会自动尝试使用不同的语言设置
- 如果问题持续存在，可以考虑使用其他语音识别服务，如百度语音识别 API
- 确保音频文件质量良好，背景噪音较少

#### 配置代理服务器

如果你的网络环境限制了对 Google 服务的访问，你可以配置代理服务器：

1. 编辑 `.env` 文件
2. 设置 `PROXY_URL` 变量，格式为：`http://username:password@proxy_host:proxy_port`
   例如：`PROXY_URL=http://myproxy.example.com:8080` 或 `PROXY_URL=http://user:pass@myproxy.example.com:8080`
3. 重启应用程序

### DeepSeek API 问题

如果遇到"调用DeepSeek API时出错"的错误，请确保：

1. 您已经在 `.env` 文件中设置了正确的 API 密钥
2. API 密钥没有过期
3. 您没有超出 API 调用限制
4. DeepSeek 服务器正常运行

## 技术栈

- Flask：Web框架
- SpeechRecognition：语音识别
- MoviePy：视频处理
- Requests：API调用
- HTML/CSS/JavaScript：前端界面
