#!/usr/bin/env python3

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeRemainingColumn

from src.utils import check_ffmpeg, find_video_files
from src.convert import convert_file
from src.config import load_config

console = Console()

@click.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path), help='Path to configuration file (defaults to ./config.yml)')
def main(input_dir: Path, output_dir: Path, config: Path):
    """
    Batch MP4 converter with M2 optimization.
    
    Recursively converts all .mp4 files using ffmpeg with optimized settings:
    - Video: H.265 (VideoToolbox), CRF 23, 10-bit
    - Audio: AAC, 128kbps
    
    The directory structure is preserved in the output folder.
    """
    if not check_ffmpeg():
        console.print("Error: ffmpeg not found")
        sys.exit(1)

    try:
        cfg = load_config(config)
    except Exception as e:
        console.print(f"Error loading config: {e}", style="red")
        sys.exit(1)
    
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print("Searching files...")
    mp4_files = find_video_files(input_dir)
    
    if not mp4_files:
        console.print("No MP4 files found")
        return
    
    console.print(f"Found {len(mp4_files)} files")
    
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
                console.print(f"Skipped: {input_file.absolute()}")
                skip_count += 1
                progress.update(task, advance=1)
                continue
            
            console.print(f"Processing: {input_file.absolute()}")
            
            # Convert the file
            if convert_file(input_file, output_file, cfg):
                success_count += 1
            else:
                fail_count += 1
            
            progress.update(task, advance=1)
    
    # Summary
    console.print(f"Complete: {success_count} success, {fail_count} failed, {skip_count} skipped")

if __name__ == '__main__':
    main()