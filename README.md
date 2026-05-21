# AutoCut

AutoCut 用语音识别为视频生成字幕，然后按你在 Markdown 文件里勾选的句子剪出新视频。整个流程不需要打开剪辑软件：转录视频，编辑文本，运行剪辑命令。

## 功能

- 从视频或音频生成 `.srt` 字幕和 `.md` 选择文件
- 在 `.md` 里勾选要保留的句子
- 按字幕时间轴剪出 `_cut.mp4` 或 `_cut.mp3`
- 支持本地 Whisper、faster-whisper 和 OpenAI Whisper API
- 支持 CUDA GPU 转录

## 安装

推荐在虚拟环境中安装，避免污染系统 Python。

```bash
git clone https://github.com/mli/autocut.git
cd autocut
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

也可以从 PyPI 安装：

```bash
pip install autocut-sub
```

额外模式按需安装：

```bash
pip install '.[faster]'  # faster-whisper
pip install '.[openai]'  # OpenAI Whisper API
pip install '.[all]'     # 全部可选依赖
```

还需要安装 `ffmpeg`：

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# macOS
brew install ffmpeg

# Windows / Scoop
scoop install ffmpeg
```

## GPU 安装

AutoCut 是否使用 GPU 取决于 PyTorch 是否能使用 CUDA。先安装与你机器匹配的 CUDA 版 PyTorch，再安装 AutoCut。

示例，CUDA 12.4：

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install .
```

检查 GPU 是否可用：

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

转录时可显式指定 GPU：

```bash
autocut -t video.mp4 --device cuda
```

如果显存不足，可以换小模型，或强制使用 CPU：

```bash
autocut -t video.mp4 --whisper-model small
autocut -t video.mp4 --device cpu
```

## Docker

CPU 镜像：

```bash
docker build -t autocut .
docker run -it --rm -v /path/to/videos:/autocut/video autocut
```

GPU 镜像：

```bash
docker build -f Dockerfile.cuda -t autocut-gpu .
docker run --gpus all -it --rm -v /path/to/videos:/autocut/video autocut-gpu
```

## 快速开始

### 1. 转录视频

```bash
autocut -t video.mp4
```

这会生成：

```text
video.srt
video.md
```

默认模型是 `small`。可以指定更快或更强的模型：

```bash
autocut -t video.mp4 --whisper-model large-v3-turbo
autocut -t video.mp4 --whisper-model medium --device cuda
```

### 2. 编辑 Markdown

打开 `video.md`，第一行表示“已经完成选择”：

```md
- [ ] <-- Mark if you are done editing.
```

改成：

```md
- [x] <-- Mark if you are done editing.
```

每条字幕前面的 `[ ]` 表示不保留，`[x]` 表示保留：

```md
- [ ] [1,00:00]   < No Speech >
- [x] [2,00:04]   这里是要保留的一句话
- [ ] [3,00:08]   这里会被剪掉
```

可以修正文案，方便自己阅读；但不要改字幕编号，例如 `[2,00:04]`。剪辑时 AutoCut 根据编号找到 `.srt` 中对应的时间段。

### 3. 剪辑视频

```bash
autocut -c video.mp4 video.srt video.md
```

输出文件：

```text
video_cut.mp4
```

覆盖已有输出：

```bash
autocut -c video.mp4 video.srt video.md --force
```

调整输出码率：

```bash
autocut -c video.mp4 video.srt video.md --bitrate 20m
```

## 常用命令

从字幕生成 Markdown 选择文件：

```bash
autocut -m video.srt video.mp4
autocut -m video.srt
```

只按 `.srt` 剪辑，不使用 Markdown：

```bash
autocut -c video.mp4 video.srt
```

生成紧凑版字幕，方便编辑：

```bash
autocut -s video.srt
```

把紧凑版字幕转回标准 `.srt`：

```bash
autocut -s video_compact.srt
```

监听一个目录，自动处理新视频：

```bash
autocut -d /path/to/videos
```

查看全部参数：

```bash
autocut --help
```

## 支持的识别模型

`--whisper-model` 支持：

```text
tiny
base
small
medium
large
large-v2
large-v3
large-v3-turbo
```

查看命令：

```bash
autocut --help | grep -A2 -- '--whisper-model'
```

模型选择建议：

- `tiny` / `base`：速度快，准确率较低
- `small`：默认选择，速度和质量较均衡
- `medium` / `large` / `large-v3`：质量更好，更慢，建议使用 GPU
- `large-v3-turbo`：速度和质量都较好的新模型

## 识别模式

默认使用本地 Whisper：

```bash
autocut -t video.mp4 --whisper-mode whisper
```

使用 faster-whisper：

```bash
pip install '.[faster]'
autocut -t video.mp4 --whisper-mode faster
```

使用 OpenAI Whisper API：

```bash
pip install '.[openai]'
export OPENAI_API_KEY=sk-...
autocut -t video.mp4 --whisper-mode openai --openai-rpm 3
```

## 字幕语言和提示词

默认输出中文：

```bash
autocut -t video.mp4 --lang zh
```

英文：

```bash
autocut -t video.mp4 --lang en
```

给 Whisper 初始提示词：

```bash
autocut -t video.mp4 --prompt "这是一段关于深度学习的视频。"
```

## 编码

默认编码是 `utf-8`。如果需要其他编码，转录和剪辑时要保持一致：

```bash
autocut -t video.mp4 --encoding gbk
autocut -c video.mp4 video.srt video.md --encoding gbk
```

## Python API

```python
from autocut import Transcribe, load_audio
```

## 项目结构

```text
autocut/
  main.py          # CLI 参数和入口
  transcribe.py    # 转录流程
  whisper_model.py # Whisper / faster-whisper / OpenAI API 适配
  cut.py           # 剪辑和合并
  utils.py         # 字幕、Markdown、音频工具
  type.py          # 模型、模式、语言定义
```
