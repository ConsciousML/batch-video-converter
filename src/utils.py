import subprocess
from pathlib import Path
from typing import List

def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def find_video_files(input_dir: Path) -> List[Path]:
    """Find all .mp4 files recursively, excluding macOS metadata files."""
    mp4_files = []
    # Search for both lowercase and uppercase .mp4 files
    for pattern in ["*.mp4", "*.MP4"]:
        for file_path in input_dir.rglob(pattern):
            # Skip macOS metadata files that start with ._
            if file_path.name.startswith("._"):
                continue
            mp4_files.append(file_path)
    return mp4_files