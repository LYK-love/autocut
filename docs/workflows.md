# Workflows

## Local Transcription and Cut

Use this when the local machine has the ASR dependencies and enough compute.

```bash
autocut -t video.mp4
```

Edit `video.md`, mark the first task as done, and check the segments to keep.

```bash
autocut -c video.mp4 video.srt video.md --force
```

## Remote ASR, Local Editing

Use this when the original media is local but ASR should run on a GPU server.
Only the extracted audio is uploaded.

```bash
autocut-harness remote-asr video.mov \
  --remote user@server \
  --remote-dir ~/videos/transcribe_jobs \
  --remote-python python
```

The command produces local `video.srt` and `video.md` files next to the original
media. Edit the Markdown locally, then cut or import into Resolve.

## DaVinci Resolve Rough Cut

Start DaVinci Resolve, open a project, and enable external scripting in Resolve
preferences. Then run:

```bash
autocut-resolve import video.mov video.srt video.md
```

AutoCut creates an editable rough-cut timeline from the selected subtitle
segments. Use Resolve for detailed trimming, grading, sound, and export.

If scripting is unavailable:

```bash
autocut-resolve export-fcpxml video.mov video.srt video.md
```

Import the generated FCPXML in Resolve.

## AI-Assisted Markdown Review

AutoCut does not require AI review, but `.md` files are intentionally plain text.
An AI assistant can inspect repeated takes, mark the best complete version, and
lightly correct ASR text while preserving subtitle ID tokens such as `[12,03:41]`.

Do not change subtitle IDs. AutoCut uses those IDs to map Markdown decisions back
to `.srt` timing.
