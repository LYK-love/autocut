import os
import tempfile
import unittest
from unittest import mock

from autocut import resolve, selection
from config import TEST_CONTENT_PATH, TEST_MEDIA_PATH


class TestSelection(unittest.TestCase):
    def test_selected_segments_from_md(self):
        segments = selection.selected_segments(
            os.path.join(TEST_CONTENT_PATH, "test.srt"),
            os.path.join(TEST_CONTENT_PATH, "test_md.md"),
        )

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["index"], 2)
        self.assertEqual(segments[0]["start"], 5.0)
        self.assertEqual(segments[0]["end"], 10.26)

    @mock.patch("autocut.resolve._frame_rate_from_media", return_value=30)
    def test_export_fcpxml(self, _):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "rough.fcpxml")
            result = resolve.export_fcpxml(
                os.path.join(TEST_MEDIA_PATH, "test001.mp4"),
                os.path.join(TEST_CONTENT_PATH, "test.srt"),
                os.path.join(TEST_CONTENT_PATH, "test_md.md"),
                output,
                "rough",
                "utf-8",
            )

            self.assertEqual(result, output)
            with open(output, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("<fcpxml", text)
            self.assertIn("autocut_0001", text)
            self.assertIn("rough", text)


if __name__ == "__main__":
    unittest.main()
