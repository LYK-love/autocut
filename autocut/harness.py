import argparse
import logging
import shlex
import subprocess
from pathlib import Path


def _run(cmd):
    logging.info("Running: %s", " ".join(shlex.quote(x) for x in cmd))
    subprocess.run(cmd, check=True)


def _remote_quote(path):
    if path == "~":
        return path
    if path.startswith("~/"):
        return "~/" + shlex.quote(path[2:])
    return shlex.quote(path)


def extract_audio(video_fn, audio_fn):
    _run(["ffmpeg", "-y", "-i", video_fn, "-vn", "-ac", "1", "-ar", "16000", audio_fn])


def prepare_remote_asr(args):
    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        raise FileNotFoundError(video)
    audio = Path(args.audio).expanduser().resolve() if args.audio else video.with_suffix(".wav")
    extract_audio(str(video), str(audio))

    remote_dir = args.remote_dir.rstrip("/")
    _run(["ssh", args.remote, f"mkdir -p {_remote_quote(remote_dir)}"])
    _run(["rsync", "-avh", "--partial", str(audio), f"{args.remote}:{remote_dir}/"])

    remote_audio = f"{remote_dir}/{audio.name}"
    remote_log = f"{remote_audio.rsplit('.', 1)[0]}.{args.whisper_mode}.log"
    remote_cmd = (
        f"cd {_remote_quote(args.remote_autocut_dir)} && "
        f"CUDA_VISIBLE_DEVICES={shlex.quote(args.cuda_visible_devices)} "
        f"{shlex.quote(args.remote_python)} -m autocut "
        f"-t {_remote_quote(remote_audio)} "
        f"--whisper-mode {shlex.quote(args.whisper_mode)} "
        f"--whisper-model {shlex.quote(args.whisper_model)} "
        f"--device {shlex.quote(args.device)} "
        f"--lang {shlex.quote(args.lang)} "
        f"--asr-max-segment-seconds {args.asr_max_segment_seconds} "
        f"--force 2>&1 | tee {_remote_quote(remote_log)}"
    )
    _run(["ssh", args.remote, remote_cmd])

    local_dir = str(video.parent)
    stem = audio.stem
    for ext in ("srt", "md"):
        _run(["rsync", "-avh", f"{args.remote}:{remote_dir}/{stem}.{ext}", local_dir + "/"])
    print(f"audio={audio}")
    print(f"remote_srt={args.remote}:{remote_dir}/{stem}.srt")
    print(f"remote_md={args.remote}:{remote_dir}/{stem}.md")
    print(f"remote_log={args.remote}:{remote_log}")
    print(f"local_srt={video.parent / (stem + '.srt')}")
    print(f"local_md={video.parent / (stem + '.md')}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the local-audio/remote-ASR AutoCut workflow"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("remote-asr")
    p.add_argument("video")
    p.add_argument("--audio", default=None)
    p.add_argument("--remote", required=True)
    p.add_argument("--remote-dir", required=True)
    p.add_argument("--remote-autocut-dir", default="~/projects/autocut")
    p.add_argument(
        "--remote-python",
        default="python",
    )
    p.add_argument("--cuda-visible-devices", default="0")
    p.add_argument("--whisper-mode", default="sensevoice")
    p.add_argument("--whisper-model", default="SenseVoiceSmall")
    p.add_argument("--device", default="cuda")
    p.add_argument("--lang", default="zh")
    p.add_argument("--asr-max-segment-seconds", default="8")

    args = parser.parse_args()
    logging.basicConfig(format="[autocut-harness] %(levelname)-6s %(message)s")
    logging.getLogger().setLevel(logging.INFO)
    if args.command == "remote-asr":
        prepare_remote_asr(args)


if __name__ == "__main__":
    main()
