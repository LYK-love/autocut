import unittest
from types import SimpleNamespace

from autocut.whisper_model import Qwen3ASRModel


class TestQwen3ASRModel(unittest.TestCase):
    def test_language_aliases(self):
        model = Qwen3ASRModel(sample_rate=16000)

        self.assertEqual(model._qwen_language("zh"), "Chinese")
        self.assertEqual(model._qwen_language("en"), "English")
        self.assertEqual(model._qwen_language("Japanese"), "Japanese")

    def test_gen_srt_uses_origin_segment_timestamps(self):
        model = Qwen3ASRModel(sample_rate=16000)

        subs = model.gen_srt(
            [
                {
                    "origin_timestamp": {"start": 32000, "end": 48000},
                    "result": [SimpleNamespace(text="你好 Qwen3 ASR")],
                }
            ]
        )

        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].content, "< No Speech >")
        self.assertEqual(subs[1].start.total_seconds(), 2.0)
        self.assertEqual(subs[1].end.total_seconds(), 3.0)
        self.assertEqual(subs[1].content, "你好 Qwen3 ASR")

    def test_extract_text_from_dict_result(self):
        model = Qwen3ASRModel(sample_rate=16000)

        self.assertEqual(model._extract_text({"text": "dict text"}), "dict text")


if __name__ == "__main__":
    unittest.main()
