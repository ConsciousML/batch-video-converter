#!/bin/bash

# Minimal MP4 Batch Converter Script
# Recursively converts all .mp4 files using optimized M2 settings
# Usage: ./convert_mp4s.sh <input_folder> <output_folder>

set -e  # Exit on any error

# Function to display usage
usage() {
    echo "Usage: $0 <input_folder> <output_folder>"
    echo ""
    echo "This script recursively finds all .mp4 files in the input folder"
    echo "and converts them using ffmpeg with M2 optimized settings:"
    echo "  - Video: H.265 (VideoToolbox), CRF 23, 10-bit"
    echo "  - Audio: AAC, 128kbps"
    echo ""
    echo "The directory structure is preserved in the output folder."
    exit 1
}

# Function to update progress bar
update_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r🎬 Progress: ["
    printf "%*s" $filled | tr ' ' '█'
    printf "%*s" $empty | tr ' ' '░'
    printf "] %d%% (%d/%d files)" $percentage $current $total
}

# Function to convert a single file
convert_file() {
    local input_file="$1"
    local output_file="$2"
    local file_num="$3"
    local total_files="$4"
    
    echo ""
    echo "📹 Converting file $file_num/$total_files: $(basename "$input_file")"
    
    # Create output directory if it doesn't exist
    mkdir -p "$(dirname "$output_file")"
    
    # Run ffmpeg conversion
    if ffmpeg -i "$input_file" \
        -c:v hevc_videotoolbox \
        -crf 23 \
        -pix_fmt p010le \
        -c:a aac \
        -b:a 128k \
        -tag:v hvc1 \
        -y \
        "$output_file" > /dev/null 2>&1; then
        
        echo "✅ SUCCESS"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Check arguments
if [ $# -ne 2 ]; then
    echo "Error: Wrong number of arguments"
    usage
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

# Validate input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Convert to absolute paths
INPUT_DIR=$(cd "$INPUT_DIR" && pwd)
OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)

echo "🎬 MP4 Batch Converter (M2 Optimized)"
echo "======================================"
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed"
    echo "Install with: brew install ffmpeg"
    exit 1
fi

# Find all .mp4 files recursively (exclude macOS metadata files)
echo "🔍 Searching for .mp4 files..."
mp4_files=()

while IFS= read -r -d '' file; do
    # Skip macOS metadata files that start with ._
    if [[ $(basename "$file") == ._* ]]; then
        continue
    fi
    mp4_files+=("$file")
done < <(find "$INPUT_DIR" -type f -iname "*.mp4" -print0)

if [ ${#mp4_files[@]} -eq 0 ]; then
    echo "No .mp4 files found in $INPUT_DIR"
    exit 0
fi

echo "Found ${#mp4_files[@]} .mp4 file(s)"
echo ""

# Initialize counters
success_count=0
fail_count=0
current_file=0

# Process each file
for input_file in "${mp4_files[@]}"; do
    ((current_file++))
    
    # Calculate relative path from input directory
    relative_path="${input_file#$INPUT_DIR/}"
    
    # Create output file path
    output_file="$OUTPUT_DIR/$relative_path"
    
    # Skip if output file already exists
    if [ -f "$output_file" ]; then
        echo "⏭️  SKIPPED ($current_file/${#mp4_files[@]}): $relative_path (already exists)"
        update_progress $current_file ${#mp4_files[@]}
        continue
    fi
    
    # Update progress
    update_progress $((current_file-1)) ${#mp4_files[@]}
    
    # Convert the file
    if convert_file "$input_file" "$output_file" $current_file ${#mp4_files[@]}; then
        ((success_count++))
    else
        ((fail_count++))
    fi
done

# Final progress update
update_progress ${#mp4_files[@]} ${#mp4_files[@]}
echo ""
echo ""

# Summary
echo "📊 SUMMARY"
echo "==========="
echo "✅ Successful: $success_count"
echo "❌ Failed: $fail_count"
echo ""
echo "🎉 Conversion complete!"
