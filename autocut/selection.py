import re

import srt

from . import utils


def load_subtitles(srt_fn, encoding="utf-8"):
    with open(srt_fn, encoding=encoding) as f:
        return list(srt.parse(f.read()))


def selected_subtitle_ids(md_fn, encoding="utf-8", require_done=True):
    md = utils.MD(md_fn, encoding)
    if require_done and not md.done_editing():
        return []

    ids = []
    for mark, sent in md.tasks():
        if not mark:
            continue
        m = re.match(r"\[(\d+)", sent.strip())
        if m:
            ids.append(int(m.group(1)))
    return ids


def selected_subtitles(srt_fn, md_fn=None, encoding="utf-8", require_done=True):
    subs = load_subtitles(srt_fn, encoding)
    if not md_fn:
        return sorted(subs, key=lambda x: x.start)

    ids = set(selected_subtitle_ids(md_fn, encoding, require_done=require_done))
    return sorted((sub for sub in subs if sub.index in ids), key=lambda x: x.start)


def subtitles_to_segments(subs, merge_gap=0.5):
    segments = []
    for sub in sorted(subs, key=lambda x: x.start):
        item = {
            "index": sub.index,
            "start": sub.start.total_seconds(),
            "end": sub.end.total_seconds(),
            "text": sub.content.strip(),
        }
        if not segments:
            segments.append(item)
            continue

        if item["start"] - segments[-1]["end"] < merge_gap:
            segments[-1]["end"] = item["end"]
            if item["text"]:
                segments[-1]["text"] = (
                    segments[-1]["text"] + "\n" + item["text"]
                ).strip()
        else:
            segments.append(item)
    return segments


def selected_segments(srt_fn, md_fn=None, encoding="utf-8", require_done=True):
    return subtitles_to_segments(
        selected_subtitles(srt_fn, md_fn, encoding, require_done=require_done)
    )
