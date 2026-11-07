# Video Date Modifier

An interactive Python CLI for changing video container metadata and file timestamps.

## Features

- Updates the container `creation_time` metadata with FFmpeg stream copying. Audio and video are not re-encoded.
- Sets file creation, access, and modification timestamps on Windows.
- Sets access and modification timestamps on other operating systems.
- Processes one video or supported video files directly inside a folder.
- Supports setting one date for all files or entering a date for each file.

## Important

The program remuxes each video to a temporary file and replaces the original file. It does not make a backup. Back up important videos before running it.

Dates are entered as `DD/MM/YYYY` and interpreted as local midnight. The container `creation_time` is stored as UTC. Folder mode does not search subfolders. If FFmpeg is unavailable or cannot update a container, file system timestamps are still attempted and the program reports the metadata failure.

## Supported containers

`mp4`, `mov`, `mkv`, `avi`

## Requirements

- Python 3.8 or newer
- FFmpeg available on `PATH`
- Python packages listed in `requirements.txt`

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/Helvior-dev/Video-Date-Modifier.git
cd Video-Date-Modifier
```

Create and activate a virtual environment, then install dependencies:

- Windows PowerShell:

  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- Linux or macOS:

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

## Usage

Run the program, enter a video path or folder, and choose a mode:

```bash
python main.py
```

1. Set one date for every supported video in the folder.
2. Enter a date separately for each video.

## Tests

Run offline tests without processing real videos or invoking FFmpeg:

```bash
python -m unittest discover -s tests -v
```
