import argparse
import asyncio
import os
import tempfile

import edge_tts
import pysubs2
from pydub import AudioSegment


async def synthesize(text, out_path, voice, rate, volume):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
    )
    await communicate.save(out_path)


async def build_dub(args):
    subs = pysubs2.load(args.srt)
    if not subs:
        raise RuntimeError("No subtitles found.")

    total_ms = int(max(line.end for line in subs))
    final_audio = AudioSegment.silent(duration=total_ms)

    tmpdir = tempfile.mkdtemp(prefix="srt_tts_")
    print(f"Temporary dir: {tmpdir}")

    for i, line in enumerate(subs):
        text = line.text.strip().replace("\\N", " ").replace("\n", " ")
        if not text:
            continue

        start_ms = int(line.start)
        end_ms = int(line.end)
        target_duration = max(1, end_ms - start_ms)
        seg_mp3 = os.path.join(tmpdir, f"{i:04d}.mp3")

        print(f"[{i + 1}/{len(subs)}] {start_ms / 1000:.2f}s: {text}")
        await synthesize(text, seg_mp3, args.voice, args.rate, args.volume)

        seg_audio = AudioSegment.from_file(seg_mp3)
        if len(seg_audio) > target_duration:
            speed = len(seg_audio) / target_duration
            seg_audio = seg_audio._spawn(
                seg_audio.raw_data,
                overrides={"frame_rate": int(seg_audio.frame_rate * speed)},
            ).set_frame_rate(seg_audio.frame_rate)

        final_audio = final_audio.overlay(seg_audio[:target_duration], position=start_ms)

    final_audio = final_audio.set_frame_rate(args.sample_rate).set_channels(args.channels)
    final_audio.export(args.output, format="wav")
    print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a draft Edge-TTS dubbing WAV from an SRT file."
    )
    parser.add_argument("srt")
    parser.add_argument("output")
    parser.add_argument("--voice", default="zh-CN-YunxiNeural")
    parser.add_argument("--rate", default="+0%")
    parser.add_argument("--volume", default="+0%")
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--channels", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(build_dub(args))


if __name__ == "__main__":
    main()
