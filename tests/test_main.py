"""Offline tests for video metadata and timestamp handling."""

import io
import os
import platform
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import main


if os.name == "nt":
    preferred_temp_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "opencode"
else:
    preferred_temp_dir = Path()
TEST_TEMP_DIR = preferred_temp_dir if preferred_temp_dir.is_dir() else Path(tempfile.gettempdir())


class VideoDateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR)
        self.addCleanup(self.temp_dir.cleanup)
        self.folder = Path(self.temp_dir.name)

    def test_video_metadata_is_written_as_utc_and_replaces_original(self):
        video = self.folder / "clip.mp4"
        video.write_bytes(b"original")
        target = datetime(2024, 5, 15, 0, 0, 0)
        expected_metadata = target.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        captured = {}

        def fake_ffmpeg(command, **_kwargs):
            captured["command"] = command
            Path(command[-1]).write_bytes(b"remuxed")
            return subprocess.CompletedProcess(command, 0)

        with patch("main.subprocess.run", side_effect=fake_ffmpeg):
            result = main.set_video_metadata(video, target)

        self.assertTrue(result)
        self.assertIn(f"creation_time={expected_metadata}", captured["command"])
        self.assertEqual(video.read_bytes(), b"remuxed")
        self.assertFalse((self.folder / "temp_clip.mp4").exists())

    def test_failed_ffmpeg_keeps_original_and_removes_temporary_file(self):
        video = self.folder / "clip.mp4"
        video.write_bytes(b"original")

        def failing_ffmpeg(command, **_kwargs):
            Path(command[-1]).write_bytes(b"partial output")
            return subprocess.CompletedProcess(command, 1)

        with patch("main.subprocess.run", side_effect=failing_ffmpeg), \
             redirect_stdout(io.StringIO()):
            result = main.set_video_metadata(video, datetime(2024, 5, 15))

        self.assertFalse(result)
        self.assertEqual(video.read_bytes(), b"original")
        self.assertFalse((self.folder / "temp_clip.mp4").exists())

    @unittest.skipUnless(platform.system() == "Windows", "Windows timestamps are platform-specific")
    def test_windows_file_times_match_local_datetime(self):
        video = self.folder / "timestamps.tmp"
        video.write_text("temporary test file", encoding="ascii")
        target = datetime(2020, 1, 2, 3, 4, 5)

        main.set_file_times_windows(video, target)

        self.assertAlmostEqual(video.stat().st_ctime, target.timestamp(), delta=2)
        self.assertAlmostEqual(video.stat().st_mtime, target.timestamp(), delta=2)

    def test_cli_runs_with_cp1252_console_encoding(self):
        missing_path = TEST_TEMP_DIR / "missing-video-date-test-folder"
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        result = subprocess.run(
            [sys.executable, "-B", str(Path(main.__file__).resolve())],
            input=f'{missing_path}\n\n',
            text=True,
            encoding="cp1252",
            capture_output=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Path does not exist.", result.stdout)


if __name__ == "__main__":
    unittest.main()
