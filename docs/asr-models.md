# ASR models

AutoCut can transcribe media with multiple ASR backends. The default CLI option
name is still `--whisper-mode` for compatibility, but it now selects the ASR
backend, not only Whisper.

## Supported backends

| Backend | `--whisper-mode` | Typical model value | Install extra | Best for | Notes |
| --- | --- | --- | --- | --- | --- |
| OpenAI Whisper local | `whisper` | `small`, `large-v3`, `large-v3-turbo` | `.[transcribe]` | General offline transcription | Default backend. Good baseline, but Chinese mixed with English technical terms may need correction. |
| faster-whisper | `faster` | `small`, `large-v3`, `large-v3-turbo` | `.[faster]` | Faster local Whisper inference | Uses the faster-whisper runtime. Keep `--device cuda` for GPU inference. |
| OpenAI Whisper API | `openai` | `whisper-1` internally | `.[openai]` | Remote API transcription | Requires `OPENAI_API_KEY`. AutoCut handles API file-size splitting. |
| SenseVoiceSmall | `sensevoice` | `SenseVoiceSmall` | `.[sensevoice]` | Chinese-heavy speech with English terms | Uses FunASR. AutoCut uses VAD timestamps, and uses sentence timestamps when FunASR provides them. |
| Qwen3-ASR-1.7B | `qwen3-asr` | `Qwen3-ASR-1.7B` | `.[qwen3-asr]` | High-accuracy multilingual local ASR | Uses the official `qwen-asr` package. AutoCut uses VAD segment timestamps; Qwen forced alignment is not wired into AutoCut yet. |

## Recommended commands

Default Whisper:

```bash
autocut -t video.mp4 --device cuda --whisper-model large-v3
```

SenseVoiceSmall:

```bash
autocut -t video.mp4 --whisper-mode sensevoice --whisper-model SenseVoiceSmall --device cuda --lang zh
```

Qwen3-ASR-1.7B:

```bash
autocut -t video.mp4 --whisper-mode qwen3-asr --whisper-model Qwen3-ASR-1.7B --device cuda --lang zh
```

## Editing text mode

AutoCut is usually used to decide what to cut. For that workflow, the transcript
should expose repeated takes instead of hiding them. Use these options when that
is more important than readable text cleanup:

```text
--asr-text-mode verbatim
--asr-max-segment-seconds 5
```

For SenseVoiceSmall, `verbatim` disables ITN and rich transcription postprocess.
For Whisper, faster-whisper, and Qwen3-ASR, there is no equivalent FunASR rich
postprocess layer, so this option has little effect beyond documenting the
editing intent.

`--asr-max-segment-seconds` is backend-independent: AutoCut splits long VAD speech
regions into shorter chunks before calling the selected ASR backend. This applies
to Whisper, faster-whisper, OpenAI Whisper API, SenseVoiceSmall, and Qwen3-ASR.
It does not guarantee recovery of repetitions already collapsed inside the ASR
model, but it reduces avoidable long-context normalization and makes repeated
takes more visible in `video.md`.

Use `readable` only when the transcript is for display rather than editing:

```bash
autocut -t video.mp4 --whisper-mode sensevoice --whisper-model SenseVoiceSmall --asr-text-mode readable
```

Audio-only server transcription:

```bash
ffmpeg -y -i video.mov -vn -ac 1 -ar 16000 video.wav
rsync -avh --progress video.wav user@server:~/videos/transcribe_jobs/

ssh user@server
cd ~/videos/transcribe_jobs
autocut -t video.wav --whisper-mode sensevoice --whisper-model SenseVoiceSmall --device cuda --lang zh
```
