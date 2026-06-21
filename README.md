# AutoCut

> You can use AI to translate or explain this document and the rest of the project's documentation in your preferred language.
>
> 你可以使用 AI 将本文档和本项目的其他文档翻译成你偏好的语言，或为你解读其中的内容。 因此仓库通常不再提供其他语言版本的平行文档。

AutoCut is a text-guided video/audio cutter.

It uses ASR model, like OpenAI whister, to transcribe a video into subtitles (`.srt` files), generates a Markdown selection file, then cuts the original media according to the sentences you mark as kept.

```text
video.mp4
  │
  │  1. transcribe
  ▼
video.srt        video.md
subtitle timing  editable selection file
  │                 │
  │                 │  2. mark sentences in Markdown
  │                 ▼
  └────────────► selected subtitle ids
                    │
                    │  3. cut original media by .srt timestamps
                    ▼
              video_cut.mp4
```

## Features

- Transcribe video/audio into `.srt` subtitles
- Generate an editable `.md` selection file
- Keep or remove sentences by checking Markdown boxes
- Cut video/audio according to subtitle timestamps
- Support local Whisper, faster-whisper, and OpenAI Whisper API
- Support CUDA GPU transcription when available

## Install

```bash
git clone https://github.com/LYK-love/autocut.git
cd autocut

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install .
```

The default install is lightweight and supports Markdown editing, `.srt` handling,
and local ffmpeg cutting. It does not install Whisper, Torch, or model weights.

Install `ffmpeg` if it is not already available:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg
```

Optional backends:

```bash
pip install '.[transcribe]'  # local Whisper transcription
pip install '.[faster]'  # faster-whisper
pip install '.[openai]'  # OpenAI Whisper API
pip install '.[all]'     # all optional dependencies
```

## Quick Start

### 1. Transcribe

```bash
autocut -t video.mp4
```

This generates:

```text
video.srt
video.md
```

`video.srt` stores subtitle timestamps.
`video.md` is the file you edit.

You can choose a different Whisper model:

```bash
autocut -t video.mp4 --whisper-model large-v3-turbo
```

Use GPU explicitly:

```bash
autocut -t video.mp4 --device cuda
```

### 2. Edit the Markdown file

Open `video.md`. It's recommended to use Typora as it's more illustrative.


You can edit the Markdown manually, or use an AI coding agent to help decide
which subtitle tasks to keep. I also maintain a companion Codex skill for this
workflow:

- https://github.com/LYK-love/autocut-skill

The skill is designed to inspect AutoCut `.md` and `.srt` files, apply editing
preferences such as keeping the last coherent take when a point is repeated, and
then run the final AutoCut cutting step.

At the top, mark editing as done:

```md
- [x] <-- Mark if you are done editing.
```

Then mark the sentences you want to keep:

```md
- [ ] [1,00:00]   This sentence will be removed.
- [x] [2,00:04]   This sentence will be kept.
- [ ] [3,00:08]   This sentence will be removed.
- [x] [4,00:12]   This sentence will be kept.
```

`[ ]` means discard.
`[x]` means keep.

You may edit the text for readability, but do not change the subtitle id such as `[2,00:04]`. AutoCut uses that id to find the corresponding timestamp in `video.srt`.

### 3. Cut

```bash
autocut -c video.mp4 video.srt video.md
```

This creates:

```text
video_cut.mp4
```

Overwrite existing output:

```bash
autocut -c video.mp4 video.srt video.md --force
```

Set output bitrate:

```bash
autocut -c video.mp4 video.srt video.md --bitrate 20m
```

## Remote Transcription, Local Cutting

If the original video is on a local machine, such as macOS, but Whisper should run
on a GPU server, do not upload the full video just to download the cut video later.
Keep the original video local, send only extracted audio to the server, then bring
the generated `.srt` and `.md` files back for local editing and cutting.

In this mode, the macOS side does not need `torch`, `torchaudio`,
`openai-whisper`, faster-whisper, or any Whisper model weights. The macOS side
only needs `ffmpeg` plus the lightweight AutoCut dependencies required for
Markdown parsing and cutting. All ASR dependencies stay on the GPU server.

This keeps network transfer small and uses each machine for the part it is good at:

```text
macOS:
  original video
  extract audio
  edit Markdown
  run ffmpeg cutting
  no torch / whisper

GPU server:
  receive audio only
  run Whisper
  produce .srt and .md
```

### 1. Extract audio on macOS

```bash
ffmpeg -i video.mov -vn -ac 1 -ar 16000 video.wav
```

### 2. Send the audio to the GPU server

```bash
rsync -avh video.wav user@server:~/videos/transcribe_jobs/
```

### 3. Transcribe on the GPU server

The server environment needs the transcription dependencies:

```bash
pip install '.[transcribe]'
```

```bash
cd ~/videos/transcribe_jobs
autocut -t video.wav --device cuda --whisper-model large-v3 --lang zh
```

This creates:

```text
video.srt
video.md
```

### 4. Bring subtitle files back to macOS

```bash
rsync -avh user@server:~/videos/transcribe_jobs/video.srt .
rsync -avh user@server:~/videos/transcribe_jobs/video.md .
```

### 5. Edit and cut locally

Edit `video.md` on macOS, mark the kept lines with `[x]`, and mark the first line
as done:

```md
- [x] <-- Mark if you are done editing.
```

Then cut the original local video:

```bash
autocut -c video.mov video.srt video.md --bitrate 20m
```

The output is:

```text
video_cut.mp4
```

## Workflow Summary

```text
Command:
  autocut -t video.mp4

Output:
  video.srt  # subtitle timing
  video.md   # editable selection file

User:
  edit video.md
  mark kept sentences with [x]

Command:
  autocut -c video.mp4 video.srt video.md

Output:
  video_cut.mp4
```

## Common Commands

Generate Markdown from an existing `.srt` file:

```bash
autocut -m video.srt video.mp4
```

Cut using all subtitle segments in `.srt`, without Markdown selection:

```bash
autocut -c video.mp4 video.srt
```

Transcribe in English:

```bash
autocut -t video.mp4 --lang en
```

Transcribe in Chinese:

```bash
autocut -t video.mp4 --lang zh
```

Use faster-whisper:

```bash
autocut -t video.mp4 --whisper-mode faster
```

Use OpenAI Whisper API:

```bash
export OPENAI_API_KEY=sk-...
autocut -t video.mp4 --whisper-mode openai
```

Watch a folder and process new files:

```bash
autocut -d /path/to/videos
```

Show all options:

```bash
autocut --help
```

## Whisper Models

Common model choices:

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

Suggested usage:

- `tiny` / `base`: fastest, lower accuracy
- `small`: default, balanced speed and quality
- `medium` / `large` / `large-v3`: better quality, slower
- `large-v3-turbo`: strong quality-speed tradeoff

## Notes

- The `.srt` file is normally not modified during cutting.
- The `.md` file controls which subtitle segments are kept.
- The final cut is produced from the original media, not from the subtitle text.
- Adjacent selected subtitle segments may be merged to avoid overly fragmented cuts.

## Project Structure

```text
autocut/
  main.py          # CLI entry point
  transcribe.py    # ASR transcription workflow
  whisper_model.py # Whisper backend adapters
  cut.py           # cutting and merging
  utils.py         # subtitle, Markdown, and media utilities
  type.py          # model and mode definitions
```
