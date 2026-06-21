import logging
import os
import re
import subprocess
import tempfile

import srt

from . import utils


# Merge videos
class Merger:
    def __init__(self, args):
        self.args = args

    def write_md(self, videos):
        md = utils.MD(self.args.inputs[0], self.args.encoding)
        num_tasks = len(md.tasks())
        # Not overwrite if already marked as down or no new videos
        if md.done_editing() or num_tasks == len(videos) + 1:
            return

        md.clear()
        md.add_done_editing(False)
        md.add("\nSelect the files that will be used to generate `autocut_final.mp4`\n")
        base = lambda fn: os.path.basename(fn)
        for f in videos:
            md_fn = utils.change_ext(f, "md")
            video_md = utils.MD(md_fn, self.args.encoding)
            # select a few words to scribe the video
            desc = ""
            if len(video_md.tasks()) > 1:
                for _, t in video_md.tasks()[1:]:
                    m = re.findall(r"\] (.*)", t)
                    if m and "no speech" not in m[0].lower():
                        desc += m[0] + " "
                    if len(desc) > 50:
                        break
            md.add_task(
                False,
                f'[{base(f)}]({base(md_fn)}) {"[Edited]" if video_md.done_editing() else ""} {desc}',
            )
        md.write()

    def run(self):
        from moviepy import editor

        md_fn = self.args.inputs[0]
        md = utils.MD(md_fn, self.args.encoding)
        if not md.done_editing():
            return

        videos = []
        for m, t in md.tasks():
            if not m:
                continue
            m = re.findall(r"\[(.*)\]", t)
            if not m:
                continue
            fn = os.path.join(os.path.dirname(md_fn), m[0])
            logging.info(f"Loading {fn}")
            videos.append(editor.VideoFileClip(fn))

        dur = sum([v.duration for v in videos])
        logging.info(f"Merging into a video with {dur / 60:.1f} min length")

        merged = editor.concatenate_videoclips(videos)
        fn = os.path.splitext(md_fn)[0] + "_merged.mp4"
        merged.write_videofile(
            fn, audio_codec="aac", bitrate=self.args.bitrate
        )  # logger=None,
        logging.info(f"Saved merged video to {fn}")


# Cut media
class Cutter:
    def __init__(self, args):
        self.args = args

    def _write_concat_file(self, media_fn, segments):
        fd, concat_fn = tempfile.mkstemp(suffix=".ffconcat", text=True)
        with os.fdopen(fd, "w", encoding=self.args.encoding) as f:
            f.write("ffconcat version 1.0\n")
            media_fn = os.path.abspath(media_fn).replace("'", "'\\''")
            for s in segments:
                f.write(f"file '{media_fn}'\n")
                f.write(f"inpoint {s['start']:.3f}\n")
                f.write(f"outpoint {s['end']:.3f}\n")
        return concat_fn

    def _run_ffmpeg_cut(self, media_fn, output_fn, segments, is_video_file):
        if not segments:
            logging.warning("No segments selected, skip cutting")
            return

        concat_fn = self._write_concat_file(media_fn, segments)
        try:
            total = sum(s["end"] - s["start"] for s in segments)
            logging.info(
                f"Cutting {len(segments)} segments into {output_fn}, "
                f"estimated duration {total / 60:.1f} min"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_fn,
            ]
            if is_video_file:
                cmd += [
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0?",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-b:v",
                    self.args.bitrate,
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-movflags",
                    "+faststart",
                ]
            else:
                cmd += ["-vn", "-c:a", "libmp3lame", "-b:a", self.args.bitrate]
            cmd.append(output_fn)
            subprocess.run(cmd, check=True)
        finally:
            os.remove(concat_fn)

    def run(self):
        fns = {"srt": None, "media": None, "md": None}
        for fn in self.args.inputs:
            ext = os.path.splitext(fn)[1][1:]
            fns[ext if ext in fns else "media"] = fn

        assert fns["media"], "must provide a media filename"
        assert fns["srt"], "must provide a srt filename"

        is_video_file = utils.is_video(fns["media"].lower())
        outext = "mp4" if is_video_file else "mp3"
        output_fn = utils.change_ext(utils.add_cut(fns["media"]), outext)
        if utils.check_exists(output_fn, self.args.force):
            return

        with open(fns["srt"], encoding=self.args.encoding) as f:
            subs = list(srt.parse(f.read()))

        if fns["md"]:
            md = utils.MD(fns["md"], self.args.encoding)
            if not md.done_editing():
                return
            index = []
            for mark, sent in md.tasks():
                if not mark:
                    continue
                m = re.match(r"\[(\d+)", sent.strip())
                if m:
                    index.append(int(m.groups()[0]))
            subs = [s for s in subs if s.index in index]
            logging.info(f'Cut {fns["media"]} based on {fns["srt"]} and {fns["md"]}')
        else:
            logging.info(f'Cut {fns["media"]} based on {fns["srt"]}')

        segments = []
        # Avoid disordered subtitles
        subs.sort(key=lambda x: x.start)
        for x in subs:
            if len(segments) == 0:
                segments.append(
                    {"start": x.start.total_seconds(), "end": x.end.total_seconds()}
                )
            else:
                if x.start.total_seconds() - segments[-1]["end"] < 0.5:
                    segments[-1]["end"] = x.end.total_seconds()
                else:
                    segments.append(
                        {"start": x.start.total_seconds(), "end": x.end.total_seconds()}
                    )

        self._run_ffmpeg_cut(fns["media"], output_fn, segments, is_video_file)
        logging.info(f"Saved media to {output_fn}")
