import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import Config

def convert_file(input_file: Path, output_file: Path, config: Config) -> Dict[str, Any]:
    """Convert a single MP4 file using ffmpeg with M2 optimized settings.
    
    Args:
        input_file: Path to input video file.
        output_file: Path to output video file.
        config: Configuration object with conversion settings.
        
    Returns:
        Dictionary with conversion result:
        - success: bool indicating if conversion succeeded
        - error_output: str with FFmpeg stderr if conversion failed
    """
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Build FFmpeg command from configuration
    cmd = [
        'ffmpeg',
        '-i', str(input_file),
        '-c:v', config.video.codec,
        '-crf', str(config.video.crf),
        '-pix_fmt', config.video.pixel_format,
        '-c:a', config.audio.codec,
        '-b:a', config.audio.bitrate,
        '-tag:v', config.video.tag,
    ]
    
    # Add overwrite flag if configured
    if config.processing.overwrite_output:
        cmd.append('-y')
    
    cmd.append(str(output_file))
    
    try:
        # Run ffmpeg and capture output
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        return {
            "success": True,
            "error_output": None
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error_output": e.stderr if e.stderr else str(e)
        }