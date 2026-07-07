# CLI Reference

AutoCut provides three command-line entry points:

- `autocut`: transcribe, create Markdown selection files, and cut media.
- `autocut-resolve`: create DaVinci Resolve rough cuts from AutoCut output.
- `autocut-harness`: coordinate local audio extraction and remote ASR jobs.

All commands support `--help`.

## `autocut`

Transcribe media into `.srt` and `.md`:

```bash
autocut -t video.mp4
```

Create Markdown from an existing subtitle file:

```bash
autocut -m video.srt video.mp4
```

Cut media from checked Markdown tasks:

```bash
autocut -c video.mp4 video.srt video.md --force
```

Useful cutting options:

```bash
--bitrate 20m
--video-encoder auto
--video-decoder none
```

Useful ASR options:

```bash
--whisper-mode sensevoice
--whisper-model SenseVoiceSmall
--device cuda
--lang zh
--asr-text-mode readable
--asr-max-segment-seconds 8
```

## `autocut-resolve`

Create a rough-cut timeline in a running DaVinci Resolve project:

```bash
autocut-resolve import video.mov video.srt video.md
```

Export FCPXML when the Resolve scripting bridge is unavailable:

```bash
autocut-resolve export-fcpxml video.mov video.srt video.md --output video_rough.fcpxml
```

Install a user-level macOS Resolve script menu item:

```bash
autocut-resolve install-script
```

## `autocut-harness`

Extract local audio, upload it to a remote server, run ASR there, and download
the generated `.srt` and `.md` files:

```bash
autocut-harness remote-asr video.mov \
  --remote user@server \
  --remote-dir ~/videos/transcribe_jobs \
  --remote-python python
```

Use `--remote-python` when the remote server requires a specific virtualenv or
conda interpreter.
