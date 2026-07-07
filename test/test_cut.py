import logging
import os
import unittest
from unittest import mock

from parameterized import parameterized, param

from autocut.cut import Cutter
from config import TestArgs, TEST_MEDIA_PATH, TEST_MEDIA_FILE_SIMPLE, TEST_CONTENT_PATH


class TestCut(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.info("检查测试文件是否正常存在")
        scan_file = os.listdir(TEST_MEDIA_PATH)
        logging.info(
            "应存在文件列表："
            + str(TEST_MEDIA_FILE_SIMPLE)
            + "  扫描到文件列表："
            + str(scan_file)
        )
        for file in TEST_MEDIA_FILE_SIMPLE:
            assert file in scan_file

    def tearDown(self):
        for file in TEST_MEDIA_FILE_SIMPLE:
            namepart = os.path.join(
                TEST_MEDIA_PATH, os.path.splitext(file)[0] + "_cut."
            )
            if os.path.exists(namepart + "mp4"):
                os.remove(namepart + "mp4")
            if os.path.exists(namepart + "mp3"):
                os.remove(namepart + "mp3")

    @parameterized.expand([param(file) for file in TEST_MEDIA_FILE_SIMPLE])
    def test_srt_cut(self, file_name):
        args = TestArgs()
        args.inputs = [
            os.path.join(TEST_MEDIA_PATH, file_name),
            os.path.join(TEST_CONTENT_PATH, "test_srt.srt"),
        ]
        cut = Cutter(args)
        cut.run()
        namepart = os.path.join(
            TEST_MEDIA_PATH, os.path.splitext(file_name)[0] + "_cut."
        )
        self.assertTrue(
            os.path.exists(namepart + "mp4") or os.path.exists(namepart + "mp3")
        )

    @parameterized.expand([param(file) for file in TEST_MEDIA_FILE_SIMPLE])
    def test_md_cut(self, file_name):
        args = TestArgs()
        args.inputs = [
            TEST_MEDIA_PATH + file_name,
            os.path.join(TEST_CONTENT_PATH, "test.srt"),
            os.path.join(TEST_CONTENT_PATH, "test_md.md"),
        ]
        cut = Cutter(args)
        cut.run()
        namepart = os.path.join(
            TEST_MEDIA_PATH, os.path.splitext(file_name)[0] + "_cut."
        )
        self.assertTrue(
            os.path.exists(namepart + "mp4") or os.path.exists(namepart + "mp3")
        )

    @mock.patch("autocut.cut.platform.system", return_value="Linux")
    def test_auto_video_encoder_falls_back_to_libx264(self, _):
        args = TestArgs()
        args.video_encoder = "auto"
        cut = Cutter(args)

        self.assertEqual(cut._select_video_encoder(), "libx264")

    def test_libx264_video_encoder_args(self):
        args = TestArgs()
        args.video_encoder = "libx264"
        cut = Cutter(args)

        self.assertEqual(cut._select_video_encoder(), "libx264")
        self.assertIn("-preset", cut._video_encoder_args())
        self.assertIn("libx264", cut._video_encoder_args())

    @mock.patch("autocut.cut.Cutter._ffmpeg_encoder_available", return_value=True)
    @mock.patch("autocut.cut.platform.system", return_value="Darwin")
    def test_auto_video_encoder_uses_videotoolbox_on_macos(self, *_):
        args = TestArgs()
        args.video_encoder = "auto"
        cut = Cutter(args)

        encoder_args = cut._video_encoder_args()
        self.assertEqual(cut._select_video_encoder(), "h264_videotoolbox")
        self.assertIn("h264_videotoolbox", encoder_args)
        self.assertNotIn("-preset", encoder_args)

    @mock.patch("autocut.cut.Cutter._ffmpeg_encoder_available", return_value=False)
    @mock.patch("autocut.cut.platform.system", return_value="Darwin")
    def test_explicit_videotoolbox_requires_encoder_support(self, *_):
        args = TestArgs()
        args.video_encoder = "h264_videotoolbox"
        cut = Cutter(args)

        with self.assertRaisesRegex(RuntimeError, "h264_videotoolbox"):
            cut._select_video_encoder()

    @mock.patch("autocut.cut.platform.system", return_value="Linux")
    def test_auto_video_decoder_falls_back_to_none(self, _):
        args = TestArgs()
        args.video_decoder = "auto"
        cut = Cutter(args)

        self.assertEqual(cut._select_video_decoder(), "none")
        self.assertEqual(cut._video_decoder_args(), [])

    @mock.patch("autocut.cut.Cutter._ffmpeg_hwaccel_available", return_value=True)
    @mock.patch("autocut.cut.platform.system", return_value="Darwin")
    def test_auto_video_decoder_uses_videotoolbox_on_macos(self, *_):
        args = TestArgs()
        args.video_decoder = "auto"
        cut = Cutter(args)

        self.assertEqual(cut._select_video_decoder(), "videotoolbox")
        self.assertEqual(cut._video_decoder_args(), ["-hwaccel", "videotoolbox"])

    @mock.patch("autocut.cut.Cutter._ffmpeg_hwaccel_available", return_value=False)
    @mock.patch("autocut.cut.platform.system", return_value="Darwin")
    def test_explicit_videotoolbox_decoder_requires_hwaccel_support(self, *_):
        args = TestArgs()
        args.video_decoder = "videotoolbox"
        cut = Cutter(args)

        with self.assertRaisesRegex(RuntimeError, "VideoToolbox hardware decode"):
            cut._select_video_decoder()
