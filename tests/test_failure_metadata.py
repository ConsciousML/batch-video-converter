#!/usr/bin/env python3

import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

from script import main
from src.metadata import MetadataManager
from src.config import load_config
from src.utils import find_video_files


def test_failure_metadata():
    """Test that failed video conversions are properly tracked in metadata."""
    runner = CliRunner()
    
    # Use empty video files that will cause FFmpeg to fail
    input_dir = Path("data/test_videos_empty")
    config_path = Path("configs/config_test.yaml")
    
    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = Path(temp_output_dir)
        
        # First run - should fail
        result = runner.invoke(main, [
            str(input_dir),
            str(output_dir), 
            '--config', str(config_path)
        ])
        
        # Command should complete (exit code 0) even with failures
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        
        # Should report failures
        assert "failed" in result.output.lower(), "No failures reported in output"
        assert "error information saved" in result.output.lower(), "No metadata file reference in output"
        
        # Load config and verify no output files were created (due to failure)
        config = load_config(config_path)
        output_files = []
        for extension in config.files.input_extensions:
            output_files.extend(output_dir.rglob(f"*{extension}"))
        assert len(output_files) == 0, "Output files were created despite failure"
        
        # Check that metadata file was created and contains failure info
        metadata_manager = MetadataManager(output_dir)
        metadata_manager.initialize(input_dir)
        
        # Verify metadata file exists
        assert metadata_manager.metadata_file.exists(), "Metadata file was not created"
        
        # Load and validate metadata structure
        with open(metadata_manager.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check basic metadata structure
        assert "input_dir" in metadata, "Metadata missing input_dir field"
        assert "last_updated" in metadata, "Metadata missing last_updated field"
        assert "processed_files" in metadata, "Metadata missing processed_files field"
        
        # Verify input_dir is set correctly
        assert metadata["input_dir"] == str(input_dir.absolute()), "Metadata input_dir mismatch"
        
        # Verify processed_files contains failure entries
        processed_files = metadata["processed_files"]
        assert len(processed_files) > 0, "No processed files recorded in metadata"
        
        # Check that each processed file entry has failure fields
        for file_path, file_metadata in processed_files.items():
            assert "processed_at" in file_metadata, f"Missing processed_at for {file_path}"
            assert "status" in file_metadata, f"Missing status for {file_path}"
            assert file_metadata["status"] == "failed", f"Status should be 'failed' for {file_path}"
            assert "error_output" in file_metadata, f"Missing error_output for {file_path}"
            assert file_metadata["error_output"] is not None, f"Error output should not be None for {file_path}"
            assert len(file_metadata["error_output"]) > 0, f"Error output should not be empty for {file_path}"
        
        # Test get_failed_files method
        failed_files = metadata_manager.get_failed_files()
        assert len(failed_files) > 0, "get_failed_files() returned no failures"
        assert len(failed_files) == len(processed_files), "get_failed_files() count mismatch"
        
        # Verify failed files structure
        for file_path, file_metadata in failed_files.items():
            assert file_metadata["status"] == "failed", f"get_failed_files() returned non-failed file: {file_path}"
            assert "error_output" in file_metadata, f"Failed file missing error_output: {file_path}"


def test_failure_retry_behavior():
    """Test that failed files are automatically retried on subsequent runs."""
    runner = CliRunner()
    
    input_dir = Path("data/test_videos_empty")
    config_path = Path("configs/config_test.yaml")
    
    with tempfile.TemporaryDirectory() as temp_output_dir:
        output_dir = Path(temp_output_dir)
        
        # First run - should fail
        result1 = runner.invoke(main, [
            str(input_dir),
            str(output_dir), 
            '--config', str(config_path)
        ])
        
        assert result1.exit_code == 0, "First run failed"
        assert "failed" in result1.output.lower(), "First run should report failures"
        
        # Second run - should retry the failed files
        result2 = runner.invoke(main, [
            str(input_dir),
            str(output_dir), 
            '--config', str(config_path)
        ])
        
        assert result2.exit_code == 0, "Second run failed"
        
        # Should show processing (retry) rather than skipping
        assert "Processing:" in result2.output, "Second run should retry failed files"
        assert "Already processed:" not in result2.output, "Failed files should not be skipped"
        
        # Should still report failures since empty files will fail again
        assert "failed" in result2.output.lower(), "Second run should report failures again"