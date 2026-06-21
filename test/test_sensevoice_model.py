import unittest

from autocut import utils
from autocut.whisper_model import SenseVoiceModel


class TestSenseVoiceModel(unittest.TestCase):
    def test_gen_srt_with_sentence_timestamps(self):
        model = SenseVoiceModel(sample_rate=16000)
        model.postprocess = lambda x: x

        subs = model.gen_srt(
            [
                {
                    "origin_timestamp": {"start": 32000, "end": 80000},
                    "result": [
                        {
                            "sentence_info": [
                                {"start": 0, "end": 1200, "text": "你好 AutoCut"},
                                {"start": 1500, "end": 2600, "text": "这是 SenseVoice"},
                            ]
                        }
                    ],
                }
            ]
        )

        self.assertEqual(len(subs), 3)
        self.assertEqual(subs[0].content, "< No Speech >")
        self.assertEqual(subs[1].start.total_seconds(), 2.0)
        self.assertEqual(subs[1].end.total_seconds(), 3.2)
        self.assertEqual(subs[1].content, "你好 AutoCut")
        self.assertEqual(subs[2].start.total_seconds(), 3.5)
        self.assertEqual(subs[2].end.total_seconds(), 4.6)
        self.assertEqual(subs[2].content, "这是 SenseVoice")

    def test_gen_srt_without_timestamps_uses_origin_segment(self):
        model = SenseVoiceModel(sample_rate=16000)
        model.postprocess = lambda x: x

        subs = model.gen_srt(
            [
                {
                    "origin_timestamp": {"start": 32000, "end": 48000},
                    "result": [{"text": "没有句级时间戳"}],
                }
            ]
        )

        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].content, "< No Speech >")
        self.assertEqual(subs[1].start.total_seconds(), 2.0)
        self.assertEqual(subs[1].end.total_seconds(), 3.0)
        self.assertEqual(subs[1].content, "没有句级时间戳")

    def test_verbatim_mode_does_not_apply_postprocess(self):
        model = SenseVoiceModel(sample_rate=16000)
        model.postprocess = lambda x: "changed"
        model.configure(text_mode="verbatim", max_segment_seconds=5.0)

        subs = model.gen_srt(
            [
                {
                    "origin_timestamp": {"start": 0, "end": 16000},
                    "result": [{"text": "重复 重复 重复"}],
                }
            ]
        )

        self.assertEqual(subs[0].content, "重复 重复 重复")

    def test_split_segment_uses_max_segment_seconds(self):
        segments = utils.split_long_segments(
            [{"start": 0, "end": 12 * 16000}], 5 * 16000
        )

        self.assertEqual(
            segments,
            [
                {"start": 0, "end": 5 * 16000},
                {"start": 5 * 16000, "end": 10 * 16000},
                {"start": 10 * 16000, "end": 12 * 16000},
            ],
        )


if __name__ == "__main__":
    unittest.main()
