import os
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime, timezone
from tqdm import tqdm

if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes

    def set_file_times_windows(path, new_date):
        FILE_WRITE_ATTRIBUTES = 0x100
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        kernel32.CreateFileW.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.SetFileTime.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        )
        kernel32.SetFileTime.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.CreateFileW(
            str(path), FILE_WRITE_ATTRIBUTES, 0, None, 3, 0, None
        )
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), f"Could not open file for timestamp update: {path}")

        utc_date = new_date.astimezone(timezone.utc)
        delta = utc_date - datetime(1601, 1, 1, tzinfo=timezone.utc)
        filetime_ticks = (
            (delta.days * 86400 + delta.seconds) * 10**7
            + delta.microseconds * 10
        )
        file_time = wintypes.FILETIME(
            filetime_ticks & 0xFFFFFFFF,
            filetime_ticks >> 32,
        )

        try:
            if not kernel32.SetFileTime(
                handle,
                ctypes.byref(file_time),
                ctypes.byref(file_time),
                ctypes.byref(file_time),
            ):
                raise OSError(ctypes.get_last_error(), f"Could not set file timestamps: {path}")
        finally:
            kernel32.CloseHandle(handle)
else:
    def set_file_times_windows(path, new_date):
        pass


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def set_video_metadata(file_path: Path, new_date: datetime) -> bool:
    iso_date = new_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
            print(f"Warning: FFmpeg could not update metadata for {file_path.name}.")
            return False
    except Exception as e:
        print(f"\nError modifying video metadata for {file_path.name}: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False


def apply_date_to_video(file_path: Path, new_date: datetime):
    # 1. Update FFmpeg metadata creation_time
    ffmpeg_ok = set_video_metadata(file_path, new_date)

    # 2. Update File system creation / modification dates
    if platform.system() == "Windows":
        try:
            set_file_times_windows(file_path, new_date)
        except Exception as e:
            print(f"Warning: Could not update file timestamps for {file_path.name}: {e}")
    else:
        ts = new_date.timestamp()
        os.utime(file_path, (ts, ts))

    return ffmpeg_ok


def main():
    print("=" * 60)
    print(" Video Date & Metadata Modifier")
    print("=" * 60)

    if not check_ffmpeg():
        print("Warning: 'ffmpeg' was not found in system PATH.")
        print("File system timestamps will be updated, but container metadata will not.")

    raw_path = input("Enter path to video file or folder: ").strip().strip('"')
    path = Path(raw_path)

    if not path.exists():
        print("Error: Path does not exist.")
        return

    video_exts = {".mp4", ".mov", ".mkv", ".avi"}

    if path.is_file():
        if path.suffix.lower() not in video_exts:
            print(f"Error: Unsupported video format: {path.suffix}")
            return
        files = [path]
    else:
        files = [f for f in path.glob("*") if f.suffix.lower() in video_exts]

    if not files:
        print("No video files found (.mp4, .mov, .mkv, .avi).")
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
            print("Invalid date format. Use DD/MM/YYYY.")
            return

        for f in tqdm(files, desc="Processing videos", ascii=True):
            apply_date_to_video(f, new_date)

    elif mode == "2":
        for f in files:
            print(f"\nFile: {f.name}")
            date_str = input("Enter new date (DD/MM/YYYY): ").strip()
            try:
                new_date = datetime.strptime(date_str, "%d/%m/%Y")
                metadata_updated = apply_date_to_video(f, new_date)
                if metadata_updated:
                    print(f"Updated {f.name}")
                else:
                    print(f"File timestamps updated, but container metadata failed for {f.name}.")
            except ValueError:
                print("Skipped due to invalid date format.")
    else:
        print("Invalid mode choice.")
        return

    print("\nAll video date processing complete.")


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
