# Dubbing from Cut Subtitles

This document describes an optional post-processing workflow: generate a draft
dubbing track from subtitles after AutoCut has already produced a cut video.

Typical inputs:

```text
video_cut.mp4
video_cut.srt
```

Typical outputs:

```text
video_cut_voice.wav
video_cut_dub.mp4
```

Use the cut subtitle file, not the original subtitle file. After cutting, the
timeline has changed, so the original subtitles no longer match the cut video.

## Edge-TTS Draft Voice

The repository includes a small example script:

```bash
python scripts/srt_to_dub.py video_cut.srt video_cut_voice.wav \
  --voice zh-CN-YunxiNeural \
  --rate +8%
```

The script requires optional dependencies that are not part of the default
AutoCut install:

```bash
pip install edge-tts pysubs2 pydub
```

Install `ffmpeg` as well; `pydub` uses it for audio decoding.

## Replace the Video Audio Track

After generating the WAV file, replace the original audio track:

```bash
ffmpeg -y \
  -i video_cut.mp4 \
  -i video_cut_voice.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -shortest \
  video_cut_dub.mp4
```

Preview with subtitles:

```bash
mpv --sub-file=video_cut.srt video_cut_dub.mp4
```

## Custom TTS Backends

For production dubbing, use a higher-quality TTS backend or a voice-cloning
system such as GPT-SoVITS. The integration shape is the same:

1. Read `video_cut.srt`.
2. Generate a full-length audio track aligned to subtitle timestamps.
3. Replace or mix the video audio with `ffmpeg`.

Keep backend-specific model paths and API URLs in local configuration or command
arguments. Do not hardcode machine-specific paths in repository files.

## Notes

- Empty subtitle lines and `< No Speech >` markers should be skipped.
- Very short subtitle durations may require merging adjacent lines or increasing
  speech rate.
- Dubbing and subtitles are separate outputs. Replacing audio does not burn
  subtitles into the video.
