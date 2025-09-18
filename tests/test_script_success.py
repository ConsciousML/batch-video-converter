#!/usr/bin/env python3

import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

from script import main
from src.metadata import MetadataManager
from src.config import load_config
from src.utils import find_video_files


def test_success():
    """Test the main video conversion functionality with real video files."""
    runner = CliRunner()
    
    # Use relative paths from the project root
    input_dir = Path("data/test_videos_success")
    config_path = Path("configs/config_test.yaml")
    
    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = Path(temp_output_dir)
        
        # Run the main function
        result = runner.invoke(main, [
            str(input_dir),
            str(output_dir), 
            '--config', str(config_path)
        ])
        
        # Check that the command succeeded
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        
        # Load config to get file extensions for output file search
        config = load_config(config_path)
        
        # Check that output files were created (search for all configured extensions)
        output_files = []
        for extension in config.files.input_extensions:
            output_files.extend(output_dir.rglob(f"*{extension}"))
        assert len(output_files) > 0, "No output files were created"
        
        # Verify number of output files matches number of input files
        # `test.fcpbundle/empty.mp4` should be ignored
        assert len(output_files) == 2, f"Output files ({len(output_files)}) != Input files 2"
        
        # Verify the converted files exist and have reasonable sizes
        for output_file in output_files:
            assert output_file.exists(), f"Output file {output_file} does not exist"
            assert output_file.stat().st_size > 0, f"Output file {output_file} is empty"
        
        # Check that metadata file was created and is well-formed
        metadata_file = output_dir / MetadataManager.METADATA_FILENAME
        assert metadata_file.exists(), "Metadata file was not created"
        
        # Load and validate metadata structure
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check required metadata fields
        assert "input_dir" in metadata, "Metadata missing input_dir field"
        assert "last_updated" in metadata, "Metadata missing last_updated field"
        assert "processed_files" in metadata, "Metadata missing processed_files field"
        
        # Verify input_dir is set correctly
        assert metadata["input_dir"] == str(input_dir.absolute()), "Metadata input_dir mismatch"
        
        # Verify processed_files contains entries for converted files
        processed_files = metadata["processed_files"]
        assert len(processed_files) > 0, "No processed files recorded in metadata"
        
        # Check that each processed file entry has required fields
        for file_path, file_metadata in processed_files.items():
            assert "processed_at" in file_metadata, f"Missing processed_at for {file_path}"
            assert "video" in file_metadata, f"Missing video config for {file_path}"
            assert "audio" in file_metadata, f"Missing audio config for {file_path}"
            assert "processing" in file_metadata, f"Missing processing config for {file_path}"