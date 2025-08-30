# Batch Video Converter

A Python-based batch MP4 video converter optimized for Apple Silicon (M2) using FFmpeg with hardware acceleration.

## Features

- Recursive MP4 file discovery
- Hardware-accelerated H.265 encoding using VideoToolbox
- Progress tracking with visual progress bars
- Directory structure preservation
- Skip already converted files
- M2-optimized encoding settings

## Installation

### Prerequisites

1. **FFmpeg** (required for video conversion)
   ```bash
   brew install ffmpeg
   ```

2. **uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.local/bin/env  # or restart your shell
   ```

3. **Python 3.13+** (check with `python --version`)

### Install Dependencies

```bash
# Clone or navigate to the project directory
cd batch-video-converter

# Install Python dependencies
uv sync
```

## Usage

```bash
# Run the converter directly with uv
uv run script.py <input_folder> <output_folder>

# Or use the console script
uv run convert-videos <input_folder> <output_folder>
```

## Video Settings

The converter uses these M2-optimized settings:
- **Video Codec**: H.265 (HEVC) with VideoToolbox hardware acceleration
- **Quality**: CRF 23 (high quality)
- **Pixel Format**: 10-bit (p010le)
- **Audio Codec**: AAC at 128kbps
- **Container**: MP4 with hvc1 tag for better compatibility