import asyncio
import os
import tempfile
from pathlib import Path

import edge_tts
import pysubs2
from pydub import AudioSegment


SRT_PATH = "/home/lyk/video/2026-05-21/2026-05-21_cut.srt"
OUT_WAV = "/home/lyk/video/2026-05-21/2026-05-21_cut_dub.wav"

# 中文男声/女声可以换
VOICE = "zh-CN-YunxiNeural"
RATE = "+0%"
VOLUME = "+0%"


async def synthesize(text: str, out_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        volume=VOLUME,
    )
    await communicate.save(out_path)


def ms_to_silence(ms: int):
    return AudioSegment.silent(duration=max(0, ms))


async def main():
    subs = pysubs2.load(SRT_PATH)

    if not subs:
        raise RuntimeError("No subtitles found.")

    # 总时长取最后一句字幕结束时间
    total_ms = int(max(line.end for line in subs))
    final_audio = AudioSegment.silent(duration=total_ms)

    tmpdir = tempfile.mkdtemp(prefix="srt_tts_")
    print(f"Temporary dir: {tmpdir}")

    for i, line in enumerate(subs):
        text = line.text.strip()
        text = text.replace("\\N", " ").replace("\n", " ")

        if not text:
            continue

        start_ms = int(line.start)
        end_ms = int(line.end)
        target_duration = max(1, end_ms - start_ms)

        seg_mp3 = os.path.join(tmpdir, f"{i:04d}.mp3")

        print(f"[{i+1}/{len(subs)}] {start_ms/1000:.2f}s - {end_ms/1000:.2f}s: {text}")

        await synthesize(text, seg_mp3)

        seg_audio = AudioSegment.from_file(seg_mp3)

        # 如果 TTS 比字幕时间长，做轻微加速；如果短，就保持原样，后面自然留空
        if len(seg_audio) > target_duration:
            speed = len(seg_audio) / target_duration

            # pydub 的 frame_rate trick：改变播放速度
            seg_audio = seg_audio._spawn(
                seg_audio.raw_data,
                overrides={"frame_rate": int(seg_audio.frame_rate * speed)}
            ).set_frame_rate(seg_audio.frame_rate)

        # 如果仍然过长，硬截断，避免压到下一句
        seg_audio = seg_audio[:target_duration]

        final_audio = final_audio.overlay(seg_audio, position=start_ms)

    final_audio = final_audio.set_frame_rate(48000).set_channels(2)
    final_audio.export(OUT_WAV, format="wav")
    print(f"Saved: {OUT_WAV}")


if __name__ == "__main__":
    asyncio.run(main())
