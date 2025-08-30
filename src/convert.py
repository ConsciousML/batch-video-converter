import subprocess
from pathlib import Path
from src.config import Config

def convert_file(input_file: Path, output_file: Path, config: Config) -> bool:
    """Convert a single MP4 file using ffmpeg with M2 optimized settings."""
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
        # Run ffmpeg with suppressed output
        result = subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False