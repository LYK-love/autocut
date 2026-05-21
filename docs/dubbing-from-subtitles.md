# 根据字幕生成配音音轨

这篇文档说明：在已经剪辑完视频，并且已经有剪后字幕文件后，如何根据字幕生成新的配音音轨，并替换视频原声。

典型输入文件：

```text
video_cut.mp4
video_cut.srt
```

典型输出文件：

```text
video_cut_voice.wav
video_cut_dub.mp4
```

## 流程

完整流程分三步：

1. 读取剪后字幕 `video_cut.srt`
2. 用 TTS 工具把字幕文本生成配音音轨 `video_cut_voice.wav`
3. 用 `ffmpeg` 把新音轨替换进剪后视频，得到 `video_cut_dub.mp4`

注意：这里使用的是剪后字幕。不要直接用原视频字幕给剪后视频配音，因为剪辑后时间轴已经变化。

## 需要的工具

### ffmpeg

用于读取视频时长、处理音频格式、替换视频音轨。

安装：

```bash
sudo apt update
sudo apt install ffmpeg
```

检查：

```bash
ffmpeg -version
ffprobe -version
```

### Python 配音脚本

当前项目使用一个脚本把 SRT 转成完整配音音轨：

```text
/home/lyk/projects/pyvideotrans/scripts/srt_edge_dub.py
```

这个脚本支持两类 TTS 后端：

- `edge`：使用 Edge-TTS，安装简单，适合快速预览
- `gpt-sovits`：使用 GPT-SoVITS API，适合接入自定义音色，例如曼波音色

### pyVideoTrans

pyVideoTrans 是一个现成的视频翻译、字幕、配音工具。它可以作为 GUI 工具使用，也可以提供相关依赖和流程参考。

源码目录示例：

```text
/home/lyk/projects/pyvideotrans
```

启动 GUI：

```bash
cd /home/lyk/projects/pyvideotrans
uv run sp.py
```

如果当前环境无法打开 GUI，也可以直接使用上面的 `srt_edge_dub.py` 脚本。

### Edge-TTS

Edge-TTS 是最容易跑通的免费 TTS 后端。它不需要训练模型，但音色是微软提供的固定音色，不是自定义“曼波”音色。

常用中文音色：

```text
zh-CN-XiaoxiaoNeural
zh-CN-XiaoyiNeural
zh-CN-YunjianNeural
zh-CN-YunxiNeural
zh-CN-YunxiaNeural
zh-CN-YunyangNeural
```

查看可用音色：

```bash
cd /home/lyk/projects/pyvideotrans
uv run edge-tts --list-voices | grep 'zh-CN'
```

### GPT-SoVITS

GPT-SoVITS 用于自定义音色或克隆音色。如果目标是“曼波声音”，最终应该接入 GPT-SoVITS 或类似支持自定义音色的 TTS 后端。

源码目录示例：

```text
/home/lyk/projects/GPT-SoVITS
```

需要准备：

```text
GPT 权重文件：    *.ckpt
SoVITS 权重文件： *.pth
参考音频：        *.wav
参考音频文本：    参考音频中说的完整文本
```

启动 API：

```bash
cd /home/lyk/projects/GPT-SoVITS
source /home/lyk/miniconda3/etc/profile.d/conda.sh
conda activate GPTSoVits

python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

如果需要切换到自定义权重：

```bash
curl "http://127.0.0.1:9880/set_gpt_weights?weights_path=/path/to/model.ckpt"
curl "http://127.0.0.1:9880/set_sovits_weights?weights_path=/path/to/model.pth"
```

## 方法一：用 Edge-TTS 快速生成预览配音

输入示例：

```text
/home/lyk/video/2026-05-21/2026-05-21_cut.mp4
/home/lyk/video/2026-05-21/2026-05-21_cut.srt
```

生成配音音轨：

```bash
cd /home/lyk/projects/pyvideotrans

uv run python scripts/srt_edge_dub.py \
  --provider edge \
  --merge \
  --srt /home/lyk/video/2026-05-21/2026-05-21_cut.srt \
  --video /home/lyk/video/2026-05-21/2026-05-21_cut.mp4 \
  --voice zh-CN-YunjianNeural \
  --rate +8% \
  --out-wav /home/lyk/video/2026-05-21/2026-05-21_cut_edge_voice.wav
```

参数说明：

- `--provider edge`：使用 Edge-TTS
- `--merge`：合并相邻短字幕再生成配音，减少吞字
- `--voice`：选择声音
- `--rate +8%`：略微加快语速
- `--out-wav`：输出完整配音音轨

替换视频原声：

```bash
ffmpeg -y \
  -i /home/lyk/video/2026-05-21/2026-05-21_cut.mp4 \
  -i /home/lyk/video/2026-05-21/2026-05-21_cut_edge_voice.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -shortest \
  /home/lyk/video/2026-05-21/2026-05-21_cut_edge_dub.mp4
```

预览：

```bash
mpv --sub-file=/home/lyk/video/2026-05-21/2026-05-21_cut.srt \
  /home/lyk/video/2026-05-21/2026-05-21_cut_edge_dub.mp4
```

## 方法二：用 GPT-SoVITS 生成自定义音色配音

先确认 GPT-SoVITS API 已启动：

```bash
curl http://127.0.0.1:9880/docs
```

生成自定义音色音轨：

```bash
cd /home/lyk/projects/pyvideotrans

uv run python scripts/srt_edge_dub.py \
  --provider gpt-sovits \
  --merge \
  --srt /home/lyk/video/2026-05-21/2026-05-21_cut.srt \
  --video /home/lyk/video/2026-05-21/2026-05-21_cut.mp4 \
  --gpt-sovits-url http://127.0.0.1:9880 \
  --ref-audio-path /path/to/reference.wav \
  --prompt-text "参考音频里说的完整文本" \
  --prompt-lang zh \
  --text-lang zh \
  --speed-factor 1.0 \
  --out-wav /home/lyk/video/2026-05-21/2026-05-21_cut_mambo_voice.wav
```

参数说明：

- `--provider gpt-sovits`：使用 GPT-SoVITS
- `--gpt-sovits-url`：GPT-SoVITS API 地址
- `--ref-audio-path`：参考音频路径
- `--prompt-text`：参考音频对应文本，必须尽量准确
- `--prompt-lang`：参考音频语言
- `--text-lang`：要合成的字幕语言
- `--speed-factor`：GPT-SoVITS 内部语速控制

替换视频原声：

```bash
ffmpeg -y \
  -i /home/lyk/video/2026-05-21/2026-05-21_cut.mp4 \
  -i /home/lyk/video/2026-05-21/2026-05-21_cut_mambo_voice.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -shortest \
  /home/lyk/video/2026-05-21/2026-05-21_cut_mambo_dub.mp4
```

## 关于字幕合并

逐条字幕生成 TTS 容易出现两个问题：

- 字幕太短，TTS 来不及说完
- 为了卡时间被迫加速或截断，导致吞字

因此推荐使用：

```bash
--merge
```

它会把相邻短字幕临时合并成较长的 TTS 段，再放回原时间轴。这个合并只发生在生成音频时，不会修改 `.srt` 文件。

可以调整合并策略：

```bash
--max-gap-ms 700
--max-chars 90
--max-duration-ms 9000
```

含义：

- `--max-gap-ms`：相邻字幕间隔小于这个值才合并
- `--max-chars`：合并后的文本最长字符数
- `--max-duration-ms`：合并后的时间段最长时长

## 常见问题

### 生成的 wav 是否使用了原视频声音？

没有。配音音轨只来自字幕文本和 TTS 工具。

原视频声音只在最后 `ffmpeg` 替换音轨时被丢弃。命令中：

```bash
-map 0:v:0 -map 1:a:0
```

表示使用第一个输入的视频轨，使用第二个输入的音频轨。

### 为什么字幕有字，但音频里没有？

常见原因：

- 字幕内容是 `< No Speech >`，脚本会跳过
- 字幕时长太短，TTS 被加速或截断
- TTS 后端生成失败
- 参考音频或模型不稳定

建议：

- 使用 `--merge`
- 提高语速，例如 `--rate +8%`
- 修正过短字幕
- 使用质量更好的 TTS 后端

### 为什么要用剪后字幕？

剪辑后视频的时间轴已经变化。原字幕仍然对应原视频，不再对应剪后视频。给剪后视频配音时必须使用剪后字幕。

### 最终视频没有字幕怎么办？

配音和字幕是两件事。替换音轨不会自动嵌入字幕。

播放时外挂字幕：

```bash
mpv --sub-file=video_cut.srt video_cut_dub.mp4
```

如果需要把字幕烧录进视频，可以另行使用 `ffmpeg` 的 subtitles 滤镜。
