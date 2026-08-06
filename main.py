import os
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes

    def set_file_times_windows(path, new_date):
        FILE_WRITE_ATTRIBUTES = 0x100
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        CreateFile = kernel32.CreateFileW
        SetFileTime = kernel32.SetFileTime
        CloseHandle = kernel32.CloseHandle

        handle = CreateFile(str(path), FILE_WRITE_ATTRIBUTES, 0, None, 3, 0, None)

        if handle == -1:
            print(f"❌ Error opening file handle: {path}")
            return

        wintime = int((new_date - datetime(1601, 1, 1)).total_seconds() * 10**7)
        ft = wintypes.FILETIME(wintime & 0xFFFFFFFF, wintime >> 32)

        SetFileTime(handle, ctypes.byref(ft), ctypes.byref(ft), ctypes.byref(ft))
        CloseHandle(handle)
else:
    def set_file_times_windows(path, new_date):
        pass


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def set_video_metadata(file_path: Path, new_date: datetime) -> bool:
    iso_date = new_date.strftime("%Y-%m-%dT%H:%M:%S")
    temp_file = file_path.with_name(f"temp_{file_path.name}")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(file_path),
        "-metadata",
        f"creation_time={iso_date}",
        "-codec",
        "copy",
        str(temp_file),
    ]

    try:
        res = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if res.returncode == 0 and temp_file.exists():
            os.replace(temp_file, file_path)
            return True
        else:
            if temp_file.exists():
                temp_file.unlink()
            return False
    except Exception as e:
        print(f"\n❌ Error modifying video metadata for {file_path.name}: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False


def apply_date_to_video(file_path: Path, new_date: datetime):
    # 1. Update FFmpeg metadata creation_time
    ffmpeg_ok = set_video_metadata(file_path, new_date)

    # 2. Update File system creation / modification dates
    if platform.system() == "Windows":
        set_file_times_windows(file_path, new_date)
    else:
        ts = new_date.timestamp()
        os.utime(file_path, (ts, ts))

    return ffmpeg_ok


def main():
    print("=" * 60)
    print(" 🎬 Video Date & Metadata Modifier")
    print("=" * 60)

    if not check_ffmpeg():
        print("⚠️ Warning: 'ffmpeg' was not found in system PATH.")
        print("   File system timestamps will be updated, but container EXIF metadata won't.")

    raw_path = input("Enter path to video file or folder: ").strip().strip('"')
    path = Path(raw_path)

    if not path.exists():
        print("❌ Path does not exist.")
        return

    video_exts = {".mp4", ".mov", ".mkv", ".avi"}

    if path.is_file():
        if path.suffix.lower() not in video_exts:
            print(f"❌ Unsupported video format: {path.suffix}")
            return
        files = [path]
    else:
        files = [f for f in path.glob("*") if f.suffix.lower() in video_exts]

    if not files:
        print("❌ No video files found (.mp4, .mov, .mkv, .avi).")
        return

    print(f"\nFound {len(files)} video file(s).")
    print("\nSelect operation mode:")
    print("1. Set one date for all files")
    print("2. Set date for each file individually")

    mode = input("\nEnter choice (1 or 2): ").strip()

    if mode == "1":
        date_str = input("Enter date for all files (DD/MM/YYYY): ").strip()
        try:
            new_date = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            print("❌ Invalid date format. Use DD/MM/YYYY.")
            return

        for f in tqdm(files, desc="Processing videos"):
            apply_date_to_video(f, new_date)

    elif mode == "2":
        for f in files:
            print(f"\nFile: {f.name}")
            date_str = input("Enter new date (DD/MM/YYYY): ").strip()
            try:
                new_date = datetime.strptime(date_str, "%d/%m/%Y")
                apply_date_to_video(f, new_date)
                print(f"✅ Updated {f.name}")
            except ValueError:
                print("❌ Skipped due to invalid date format.")
    else:
        print("❌ Invalid mode choice.")
        return

    print("\n✅ All video date processing complete!")


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
