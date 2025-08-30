#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import click
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeRemainingColumn

console = Console()

def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def find_mp4_files(input_dir: Path) -> List[Path]:
    """Find all .mp4 files recursively, excluding macOS metadata files."""
    mp4_files = []
    for file_path in input_dir.rglob("*.mp4"):
        # Skip macOS metadata files that start with ._
        if file_path.name.startswith("._"):
            continue
        mp4_files.append(file_path)
    return mp4_files

def convert_file(input_file: Path, output_file: Path) -> bool:
    """Convert a single MP4 file using ffmpeg with M2 optimized settings."""
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # FFmpeg command with M2 optimized settings
    cmd = [
        'ffmpeg',
        '-i', str(input_file),
        '-c:v', 'hevc_videotoolbox',
        '-crf', '23',
        '-pix_fmt', 'p010le',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-tag:v', 'hvc1',
        '-y',  # Overwrite output file
        str(output_file)
    ]
    
    try:
        # Run ffmpeg with suppressed output
        result = subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@click.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
def main(input_dir: Path, output_dir: Path):
    """
    Batch MP4 converter with M2 optimization.
    
    Recursively converts all .mp4 files using ffmpeg with optimized settings:
    - Video: H.265 (VideoToolbox), CRF 23, 10-bit
    - Audio: AAC, 128kbps
    
    The directory structure is preserved in the output folder.
    """
    
    # Check if ffmpeg is installed
    if not check_ffmpeg():
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all MP4 files
    mp4_files = find_mp4_files(input_dir)
    
    if not mp4_files:
        return
    
    # Initialize counters
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # Process files with progress bar
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Converting videos...", total=len(mp4_files))
        
        for input_file in mp4_files:
            # Calculate relative path from input directory
            relative_path = input_file.relative_to(input_dir)
            
            # Create output file path
            output_file = output_dir / relative_path
            
            # Skip if output file already exists
            if output_file.exists():
                skip_count += 1
                progress.update(task, advance=1)
                continue
            
            # Convert the file
            if convert_file(input_file, output_file):
                success_count += 1
            else:
                fail_count += 1
            
            progress.update(task, advance=1)
    

if __name__ == '__main__':
    main()