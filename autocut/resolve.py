import argparse
import logging
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import escape

from . import selection, utils


DEFAULT_SCRIPT_DIR = (
    "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/"
    "Fusion/Scripts/Comp"
)


def _frame_rate_from_media(media_fn):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        media_fn,
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        logging.warning("ffprobe failed, defaulting to 30 fps")
        return Fraction(30, 1)
    value = result.stdout.strip()
    if not value or value == "0/0":
        return Fraction(30, 1)
    return Fraction(value)


def _seconds_to_frame(seconds, frame_rate):
    return int(round(seconds * float(frame_rate)))


def _frames_to_time(frames, frame_rate):
    return f"{frames * frame_rate.denominator}/{frame_rate.numerator}s"


def _resolve_script_api_paths():
    api_dir = os.environ.get(
        "RESOLVE_SCRIPT_API",
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/"
        "Developer/Scripting",
    )
    modules = os.path.join(api_dir, "Modules")
    lib = os.environ.get(
        "RESOLVE_SCRIPT_LIB",
        "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/"
        "Libraries/Fusion/fusionscript.so",
    )
    return modules, lib


def _import_resolve_module():
    modules, _ = _resolve_script_api_paths()
    if modules not in sys.path:
        sys.path.append(modules)
    try:
        import DaVinciResolveScript as dvr_script
    except ImportError as exc:
        raise RuntimeError(
            "Cannot import DaVinciResolveScript. Open Resolve once and check "
            "that RESOLVE_SCRIPT_API points to Resolve's Developer/Scripting "
            "folder."
        ) from exc
    return dvr_script


def _get_resolve():
    dvr_script = _import_resolve_module()
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        raise RuntimeError(
            "DaVinci Resolve is not reachable. Start Resolve and enable "
            "Preferences > System > General > External scripting."
        )
    return resolve


def _current_project(resolve, project_name=None):
    manager = resolve.GetProjectManager()
    project = manager.GetCurrentProject()
    if project:
        return project
    if project_name:
        project = manager.CreateProject(project_name)
        if project:
            return project
    raise RuntimeError("No current Resolve project. Open or create a project first.")


def _import_media(media_pool, media_storage, media_fn):
    clips = media_storage.AddItemListToMediaPool([media_fn])
    if not clips:
        raise RuntimeError(f"Resolve could not import media: {media_fn}")
    return clips[0]


def import_rough_cut_to_resolve(media_fn, srt_fn, md_fn, timeline_name, encoding):
    media_fn = os.path.abspath(media_fn)
    segments = selection.selected_segments(srt_fn, md_fn, encoding)
    if not segments:
        raise RuntimeError("No selected segments. Mark md tasks and set editing done.")

    frame_rate = _frame_rate_from_media(media_fn)
    resolve = _get_resolve()
    project = _current_project(resolve)
    media_pool = project.GetMediaPool()
    media_storage = resolve.GetMediaStorage()
    item = _import_media(media_pool, media_storage, media_fn)

    timeline = media_pool.CreateEmptyTimeline(timeline_name)
    if not timeline:
        raise RuntimeError(f"Could not create Resolve timeline: {timeline_name}")

    clip_infos = []
    record_frame = 0
    for seg in segments:
        start_frame = _seconds_to_frame(seg["start"], frame_rate)
        end_frame = _seconds_to_frame(seg["end"], frame_rate)
        if end_frame <= start_frame:
            continue
        clip_infos.append(
            {
                "mediaPoolItem": item,
                "startFrame": start_frame,
                "endFrame": end_frame,
                "recordFrame": record_frame,
            }
        )
        record_frame += end_frame - start_frame

    if not clip_infos:
        raise RuntimeError("Selected segments are empty after frame conversion.")

    if not media_pool.AppendToTimeline(clip_infos):
        raise RuntimeError("Resolve failed to append selected segments to timeline.")

    project.SetCurrentTimeline(timeline)
    resolve.OpenPage("edit")
    return {
        "timeline": timeline_name,
        "segments": len(clip_infos),
        "duration": record_frame / float(frame_rate),
    }


def export_fcpxml(media_fn, srt_fn, md_fn, output_fn, timeline_name, encoding):
    media_abs = os.path.abspath(media_fn)
    frame_rate = _frame_rate_from_media(media_abs)
    segments = selection.selected_segments(srt_fn, md_fn, encoding)
    if not segments:
        raise RuntimeError("No selected segments. Mark md tasks and set editing done.")

    num, den = frame_rate.numerator, frame_rate.denominator
    frame_duration = f"{den}/{num}s"
    asset_duration = max(_seconds_to_frame(seg["end"], frame_rate) for seg in segments)
    sequence_duration = sum(
        _seconds_to_frame(seg["end"] - seg["start"], frame_rate)
        for seg in segments
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE fcpxml>',
        '<fcpxml version="1.10">',
        "  <resources>",
        f'    <format id="r1" name="FFVideoFormatRateUndefined" frameDuration="{frame_duration}"/>',
        (
            f'    <asset id="r2" name="{escape(os.path.basename(media_abs))}" '
            f'src="{escape(Path(media_abs).as_uri())}" start="0s" '
            f'duration="{_frames_to_time(asset_duration, frame_rate)}" '
            'hasVideo="1" hasAudio="1" '
            'format="r1"/>'
        ),
        "  </resources>",
        "  <library>",
        '    <event name="AutoCut">',
        (
            f'      <project name="{escape(timeline_name)}"><sequence format="r1" '
            f'tcStart="0s" tcFormat="NDF" duration="'
            f'{_frames_to_time(sequence_duration, frame_rate)}">'
        ),
        "        <spine>",
    ]
    offset = 0
    for i, seg in enumerate(segments, start=1):
        start = _seconds_to_frame(seg["start"], frame_rate)
        duration = _seconds_to_frame(seg["end"] - seg["start"], frame_rate)
        if duration <= 0:
            continue
        lines.append(
            (
                f'          <asset-clip name="{escape(f"autocut_{i:04d}")}" '
                f'ref="r2" offset="{_frames_to_time(offset, frame_rate)}" '
                f'start="{_frames_to_time(start, frame_rate)}" '
                f'duration="{_frames_to_time(duration, frame_rate)}"/>'
            )
        )
        offset += duration
    lines += [
        "        </spine>",
        "      </sequence></project>",
        "    </event>",
        "  </library>",
        "</fcpxml>",
        "",
    ]
    with open(output_fn, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_fn


def install_menu_script(target_dir=DEFAULT_SCRIPT_DIR):
    target = Path(target_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    script = target / "AutoCut Import Rough Cut.py"
    script.write_text(
        """#!/usr/bin/env python3
import subprocess


def choose_file(prompt):
    script = f'POSIX path of (choose file with prompt "{prompt}")'
    return subprocess.check_output(["osascript", "-e", script], text=True).strip()


media = choose_file("Choose the original video/audio file")
srt = choose_file("Choose the AutoCut .srt file")
md = choose_file("Choose the edited AutoCut .md file")
subprocess.run(["autocut-resolve", "import", media, srt, md], check=False)
""",
        encoding="utf-8",
    )
    return str(script)


def main():
    parser = argparse.ArgumentParser(
        description="Create DaVinci Resolve rough cuts from AutoCut .srt/.md files"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("media")
    common.add_argument("srt")
    common.add_argument("md")
    common.add_argument("--encoding", default="utf-8")
    common.add_argument("--timeline-name", default=None)

    p_import = sub.add_parser("import", parents=[common])
    p_export = sub.add_parser("export-fcpxml", parents=[common])
    p_export.add_argument("--output", default=None)

    p_install = sub.add_parser("install-script")
    p_install.add_argument("--target-dir", default=DEFAULT_SCRIPT_DIR)

    args = parser.parse_args()
    logging.basicConfig(format="[autocut-resolve] %(levelname)-6s %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    if args.command == "install-script":
        print(install_menu_script(args.target_dir))
        return

    timeline_name = args.timeline_name or (
        Path(args.media).stem + "_autocut_rough"
    )
    if args.command == "import":
        result = import_rough_cut_to_resolve(
            args.media, args.srt, args.md, timeline_name, args.encoding
        )
        print(
            f"Created Resolve timeline {result['timeline']} with "
            f"{result['segments']} segments, {result['duration']:.1f}s"
        )
    elif args.command == "export-fcpxml":
        output = args.output or utils.change_ext(
            utils.add_cut(args.media), "fcpxml"
        )
        export_fcpxml(
            args.media, args.srt, args.md, output, timeline_name, args.encoding
        )
        print(output)


if __name__ == "__main__":
    main()
