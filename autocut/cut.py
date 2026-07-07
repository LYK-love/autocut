import logging
import os
import platform
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

    def _has_audio(self, media_fn):
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            media_fn,
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return bool(result.stdout.strip())

    def _ffmpeg_encoder_available(self, encoder):
        cmd = ["ffmpeg", "-hide_banner", "-encoders"]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        output = f"{result.stdout}\n{result.stderr}"
        return result.returncode == 0 and encoder in output

    def _ffmpeg_hwaccel_available(self, hwaccel):
        cmd = ["ffmpeg", "-hide_banner", "-hwaccels"]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        output = f"{result.stdout}\n{result.stderr}"
        return result.returncode == 0 and hwaccel in output

    def _select_video_encoder(self):
        encoder = getattr(self.args, "video_encoder", "auto")
        if encoder == "libx264":
            return "libx264"

        videotoolbox_available = (
            platform.system() == "Darwin"
            and self._ffmpeg_encoder_available("h264_videotoolbox")
        )

        if encoder == "h264_videotoolbox":
            if not videotoolbox_available:
                raise RuntimeError(
                    "h264_videotoolbox is only available with an ffmpeg build "
                    "that includes VideoToolbox on macOS. Use --video-encoder "
                    "auto or --video-encoder libx264 on this machine."
                )
            return "h264_videotoolbox"

        if encoder == "auto" and videotoolbox_available:
            return "h264_videotoolbox"

        return "libx264"

    def _video_encoder_args(self):
        encoder = self._select_video_encoder()
        logging.info(f"Using video encoder: {encoder}")
        if encoder == "h264_videotoolbox":
            return [
                "-c:v",
                "h264_videotoolbox",
                "-b:v",
                self.args.bitrate,
                "-pix_fmt",
                "yuv420p",
                "-allow_sw",
                "1",
                "-movflags",
                "+faststart",
            ]

        return [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            self.args.bitrate,
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]

    def _select_video_decoder(self):
        decoder = getattr(self.args, "video_decoder", "none")
        if decoder == "none":
            return "none"

        videotoolbox_available = (
            platform.system() == "Darwin"
            and self._ffmpeg_hwaccel_available("videotoolbox")
        )

        if decoder == "videotoolbox":
            if not videotoolbox_available:
                raise RuntimeError(
                    "VideoToolbox hardware decode is only available with an "
                    "ffmpeg build that includes videotoolbox hwaccel on macOS. "
                    "Use --video-decoder auto or --video-decoder none on this "
                    "machine."
                )
            return "videotoolbox"

        if decoder == "auto" and videotoolbox_available:
            return "videotoolbox"

        return "none"

    def _video_decoder_args(self):
        decoder = self._select_video_decoder()
        logging.info(f"Using video decoder: {decoder}")
        if decoder == "videotoolbox":
            return ["-hwaccel", "videotoolbox"]
        return []

    def _write_filter_script(self, segments, is_video_file, has_audio):
        fd, filter_fn = tempfile.mkstemp(suffix=".fffilter", text=True)
        with os.fdopen(fd, "w", encoding=self.args.encoding) as f:
            labels = []
            for i, s in enumerate(segments):
                start = s["start"]
                end = s["end"]
                if is_video_file:
                    f.write(
                        f"[0:v]trim=start={start:.3f}:end={end:.3f},"
                        f"setpts=PTS-STARTPTS[v{i}];\n"
                    )
                    labels.append(f"[v{i}]")
                if has_audio:
                    f.write(
                        f"[0:a]atrim=start={start:.3f}:end={end:.3f},"
                        f"asetpts=PTS-STARTPTS[a{i}];\n"
                    )
                    labels.append(f"[a{i}]")

            if is_video_file and has_audio:
                f.write(
                    "".join(labels)
                    + f"concat=n={len(segments)}:v=1:a=1[outv][outa]\n"
                )
            elif is_video_file:
                f.write(
                    "".join(labels)
                    + f"concat=n={len(segments)}:v=1:a=0[outv]\n"
                )
            else:
                f.write(
                    "".join(labels)
                    + f"concat=n={len(segments)}:v=0:a=1[outa]\n"
                )
        return filter_fn

    def _run_ffmpeg_cut(self, media_fn, output_fn, segments, is_video_file):
        if not segments:
            logging.warning("No segments selected, skip cutting")
            return

        has_audio = self._has_audio(media_fn)
        filter_fn = self._write_filter_script(segments, is_video_file, has_audio)
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
            ]
            if is_video_file:
                cmd += self._video_decoder_args()
            cmd += [
                "-i",
                media_fn,
                "-filter_complex_script",
                filter_fn,
            ]
            if is_video_file:
                cmd += ["-map", "[outv]"] + self._video_encoder_args()
                if has_audio:
                    cmd += ["-map", "[outa]", "-c:a", "aac", "-b:a", "192k"]
            else:
                cmd += ["-map", "[outa]", "-vn", "-c:a", "libmp3lame", "-b:a", self.args.bitrate]
            cmd.append(output_fn)
            subprocess.run(cmd, check=True)
        finally:
            os.remove(filter_fn)

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
