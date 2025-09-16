# Batch Video Converter

A CLI tool for batch video conversion using FFmpeg.

## What it does

Recursively processes all videos in an input directory and converts them using FFmpeg, preserving the original directory structure in the output folder.

## Features 

- Convert multiple video files with consistent settings
- Maintain organized folder structures during batch processing
- Resume interrupted conversions automatically
- Log every information about each video conversion
- Writes error logs when conversion fails

## Installation

### Prerequisites

1. **FFmpeg** (required for video conversion)
   ```bash
   brew install ffmpeg
   ```

2. **uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Install

```bash
cd batch-video-converter
uv sync
```

## Usage
Modify `config.yaml` to change FFmpeg arguments if necessary.
Read the [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html) to learn more about the convertion settings.

```bash
uv run convert-videos <input_folder> <output_folder>
```

The tool will:
- Process all `.mp4` files recursively from the input directory
- Create the same directory structure in the output folder
- Generate `.batch-video-metadata.json` to track conversion progress
- Save error logs for failed conversions in `output_dir/failed_conversions/`
- When re-run on existing output directory, it reads metadata and retries only failed videos


## Default Settings

- **Video**: H.265 (HEVC) with libx265 codec, CRF 23, 10-bit (p010le)
- **Audio**: AAC at 128kbps
- **Container**: MP4 with hvc1 compatibility tag