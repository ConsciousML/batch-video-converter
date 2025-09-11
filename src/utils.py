import subprocess
from pathlib import Path
from typing import List
from src.config import Config

def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def find_video_files(input_dir: Path, input_extensions: List[str]) -> List[Path]:
    """Find all video files recursively based on provided extensions, excluding macOS metadata files.
    
    Args:
        input_dir: Directory to search for video files.
        input_extensions: List of file extensions to search for (e.g., [".mp4", ".MP4"]).
        
    Returns:
        List of Path objects for found video files.
    """
    video_files = []
    # Search for files with provided extensions
    for extension in input_extensions:
        pattern = f"*{extension}"
        for file_path in input_dir.rglob(pattern):
            # Skip macOS metadata files that start with ._
            if file_path.name.startswith("._"):
                continue
            video_files.append(file_path)
    return video_files