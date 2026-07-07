# Design

AutoCut solves a narrow editing problem: remove unwanted spoken sections from
media by editing text instead of scrubbing a timeline.

## Goals

- Turn speech into subtitle timing data.
- Give users a simple Markdown checklist for keep/remove decisions.
- Cut original media using subtitle timestamps, not edited transcript text.
- Support remote GPU transcription while keeping original video local.
- Export editable rough cuts to DaVinci Resolve for manual finishing.

## Non-Goals

- AutoCut is not a full non-linear editor.
- AutoCut does not try to replace detailed timeline editing in Resolve.
- AutoCut does not require ASR model dependencies for local cutting.

## Core Abstractions

`video.srt`
: Subtitle timing and ASR text. Subtitle indexes are stable identifiers.

`video.md`
: Human-editable checklist. Checked subtitle IDs are kept.

Selected segments
: A normalized list of `{start, end, text}` entries derived from `.srt` plus
  `.md`. This is the boundary between text selection and output backends.

Output backend
: A consumer of selected segments. Current backends are ffmpeg cutting,
  Resolve API timeline creation, and FCPXML export.

## Control Flow

```text
media
  -> ASR backend
  -> .srt
  -> .md checklist
  -> selected subtitle IDs
  -> selected segments
  -> ffmpeg cut / Resolve timeline / FCPXML
```

Remote ASR keeps the same data model. The local machine extracts audio and sends
only that audio to a GPU server. The server returns `.srt` and `.md`; all final
cutting or Resolve import can happen locally against the original media.

## Tradeoffs

Markdown is deliberately simple. It is easy to review, edit with AI tools, and
version-control, but it is not a rich timeline format.

The Resolve integration is implemented as a harness and menu script rather than
a full Workflow Integration panel. This keeps the automation testable and useful
before investing in a heavier UI.

FCPXML export is provided as a fallback because Resolve scripting availability
depends on local Resolve preferences and installation paths.

## Extension Points

- Add a new ASR backend in `autocut/whisper_model.py`.
- Add a new selected-segment consumer beside `autocut/resolve.py`.
- Add richer Markdown review or AI correction before the segment selection step.
