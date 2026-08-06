# Video Date & Metadata Modifier 🎬📅

A fast Python CLI tool to update video creation metadata inside media containers (`.mp4`, `.mov`, `.mkv`, `.avi`) and synchronize OS file system timestamps (including Windows File Creation Time via native WinAPI).

## 🚀 Features
- **Zero Re-encoding Loss**: Uses `FFmpeg` stream copying (`-codec copy`) to modify internal `creation_time` tags without re-encoding video or audio streams.
- **Native Windows Timestamps**: Updates file creation (`SetFileTime`), modification, and access timestamps in Windows File Explorer.
- **Batch & Single File Modes**: Process single video files or whole folders at once.
- **Supported Containers**: `.mp4`, `.mov`, `.mkv`, `.avi`.
- **Progress Tracking**: Real-time progress bar powered by `tqdm`.

## 🛠️ Prerequisites
- **FFmpeg**: Required for internal container metadata updates. Must be installed and accessible via system `PATH`.

## 🛠️ Installation & Setup

1. **Navigate to project directory**:
   ```bash
   cd "Video date modifier"
   ```

2. **Create & activate virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run**:
   ```bash
   python main.py
   ```
