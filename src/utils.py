import subprocess
import re
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

def filter_ignored_files(video_files: List[Path], ignore_patterns: List[str]) -> List[Path]:
    """Filter out files and folders that match ignore patterns.

    Args:
        video_files: List of video file paths to filter.
        ignore_patterns: List of regex patterns for files/folders to ignore.

    Returns:
        List of Path objects for files that don't match any ignore pattern.
    """
    if not ignore_patterns:
        return video_files

    filtered_files = []
    for file_path in video_files:
        file_str = str(file_path)
        should_ignore = False

        for pattern in ignore_patterns:
            try:
                # Check if the pattern matches any part of the file path
                if re.search(pattern, file_str):
                    should_ignore = True
                    break
            except re.error:
                # Skip invalid regex patterns
                continue

        if not should_ignore:
            filtered_files.append(file_path)

    return filtered_files