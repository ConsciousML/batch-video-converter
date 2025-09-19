import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import Config

class MetadataManager:
    """Manages processing metadata for batch video conversion."""
    
    METADATA_FILENAME = ".batch-video-metadata.json"
    
    def __init__(self, output_dir: Path):
        """
        Initialize the metadata manager.
        
        Args:
            output_dir: Directory where output files and metadata are stored
        """
        self.output_dir = output_dir
        self.failed_folder = self.output_dir / "failed_conversions"
        self.logger = logging.getLogger(__name__)
        self.metadata_file = output_dir / self.METADATA_FILENAME
        self._metadata: Optional[Dict[str, Any]] = None
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file or create empty structure."""
        if not self.metadata_file.exists():
            self.logger.info(f"No existing metadata found at {self.metadata_file}")
            return {
                "input_dir": None,
                "last_updated": None,
                "processed_files": {}
            }
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            self.logger.info(f"Loaded metadata with {len(metadata.get('processed_files', {}))} entries")
            return metadata
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Failed to load metadata from {self.metadata_file}: {e}")
            # Return empty structure if file is corrupted
            return {
                "input_dir": None,
                "last_updated": None,
                "processed_files": {}
            }
    
    def _save_metadata(self):
        """Save metadata to file atomically."""
        if self._metadata is None:
            raise RuntimeError("Metadata not initialized. Call initialize() first.")
        
        # Update last_updated timestamp
        self._metadata["last_updated"] = datetime.now().isoformat()
        
        # Write to temporary file first, then rename for atomic operation
        temp_file = self.metadata_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
            temp_file.replace(self.metadata_file)
            self.logger.debug(f"Saved metadata to {self.metadata_file}")
        except OSError as e:
            self.logger.error(f"Failed to save metadata: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def initialize(self, input_dir: Path):
        """
        Initialize metadata for the given input directory.
        
        Args:
            input_dir: Input directory being processed
            
        Raises:
            ValueError: If input directory doesn't match existing metadata
        """
        self._metadata = self._load_metadata()
        input_dir_str = str(input_dir.absolute())
        
        if self._metadata["input_dir"] is None:
            # First time processing this output directory
            self._metadata["input_dir"] = input_dir_str
            self.logger.info(f"Initializing metadata for input directory: {input_dir_str}")
        elif self._metadata["input_dir"] != input_dir_str:
            # Input directory has changed
            raise ValueError(
                f"Input directory mismatch: metadata shows '{self._metadata['input_dir']}' "
                f"but current input is '{input_dir_str}'. "
                f"Delete {self.metadata_file} to process a different input directory."
            )
        else:
            self.logger.info(f"Using existing metadata for input directory: {input_dir_str}")
    
    def should_skip_file(self, input_file: Path, output_file: Path, current_config: Config) -> bool:
        """
        Check if file should be skipped based on metadata and current config.
        
        Args:
            input_file: Path to input file
            output_file: Path to output file
            current_config: Current conversion configuration
            
        Returns:
            True if file should be skipped, False if it needs processing
        """
        if self._metadata is None:
            raise RuntimeError("Metadata not initialized. Call initialize() first.")
        
        # Convert to absolute path and calculate relative path from input directory
        input_file = input_file.resolve()
        input_dir = Path(self._metadata["input_dir"])
        try:
            relative_path = str(input_file.relative_to(input_dir))
        except ValueError:
            self.logger.error(f"File {input_file} is not under input directory {input_dir}")
            return False
        
        # Check if output file exists
        if not output_file.exists():
            self.logger.info(f"Output file missing: {output_file}")
            return False
        
        # Check if we have metadata for this file
        processed_files = self._metadata.get("processed_files", {})
        if relative_path not in processed_files:
            self.logger.info(f"No processing record found for: {relative_path}")
            return False
        
        # Check if file failed - always retry failed files
        file_metadata = processed_files[relative_path]
        status = file_metadata.get("status", "success")
        if status == "failed":
            self.logger.info(f"Retrying previously failed file: {relative_path}")
            return False
        
        # Compare stored config with current config for successful files
        stored_config = file_metadata.copy()
        current_config_dict = current_config.model_dump()
        
        # Remove fields not relevant for comparison
        current_config_dict.pop("logging", None)
        stored_config.pop("logging", None)
        stored_config.pop("processed_at", None)
        stored_config.pop("status", None)
        stored_config.pop("error_output", None)

        current_config_dict["error_log_file_path"] = None
        
        if stored_config == current_config_dict:
            self.logger.info(f"Skipping already processed file: {relative_path}")
            return True
        else:
            self.logger.info(f"Config mismatch for {relative_path}, will reprocess")
            return False
    
    def mark_processed(self, input_file: Path, config: Config):
        """
        Mark a file as processed with the given configuration.
        
        Args:
            input_file: Path to input file that was processed
            config: Configuration used for processing
        """
        if self._metadata is None:
            raise RuntimeError("Metadata not initialized. Call initialize() first.")

        # Convert to absolute path
        input_file = input_file.resolve()
        
        # Calculate relative path from input directory
        input_dir = Path(self._metadata["input_dir"])
        try:
            relative_path = str(input_file.relative_to(input_dir))
        except ValueError:
            self.logger.error(f"File {input_file} is not under input directory {input_dir}")
            return
        
        # Store config (excluding logging section)
        config_dict = config.model_dump()
        config_dict.pop("logging", None)
        
        # Add processing timestamp and status
        config_dict["processed_at"] = datetime.now().isoformat()
        config_dict["status"] = "success"
        config_dict["error_log_file_path"] = None
        
        # Update metadata
        self._metadata["processed_files"][relative_path] = config_dict
        self.logger.info(f"Marked as processed: {relative_path}")
        
        # Save metadata immediately after marking as processed
        self._save_metadata()
    
    def mark_failed(self, input_file: Path, config: Config, error_output: str):
        """
        Mark a file as failed with the given configuration and error details.
        
        Args:
            input_file: Path to input file that failed processing
            config: Configuration used for processing
            error_output: Error output from FFmpeg
        """
        if self._metadata is None:
            raise RuntimeError("Metadata not initialized. Call initialize() first.")

        # Convert to absolute path
        input_file = input_file.resolve()
        
        # Calculate relative path from input directory
        input_dir = Path(self._metadata["input_dir"])
        try:
            relative_path = str(input_file.relative_to(input_dir))
        except ValueError:
            self.logger.error(f"File {input_file} is not under input directory {input_dir}")
            return
        
        # Store config (excluding logging section)
        config_dict = config.model_dump()
        config_dict.pop("logging", None)
        
        # Add processing timestamp, status, and error details
        config_dict["processed_at"] = datetime.now().isoformat()
        config_dict["status"] = "failed"
        
        # Update metadata
        self._metadata["processed_files"][relative_path] = config_dict
        self.logger.info(f"Marked as failed: {relative_path}")
        
        # Save error logs
        error_log_file_path = self.write_failed_logs(relative_path, error_output)
        config_dict["error_log_file_path"] = error_log_file_path

        # Save metadata immediately after marking as failed
        self._save_metadata()

    def write_failed_logs(self, file_path: str, error_output: str) -> str:
        """Write error logs for a failed file conversion to a text file.

        Args:
            file_path: Relative path of the file that failed conversion
            error_output: Error output from the conversion process

        Returns:
            str: File path of the error log file.
        """
        self.failed_folder.mkdir(exist_ok=True)

        safe_filename = file_path.replace('/', '_').replace('\\', '_')

        error_log_file_path = f'{self.failed_folder / safe_filename}.txt'
        with open(error_log_file_path, 'w') as file:
            file.write(f"{error_output}\n")
        return error_log_file_path
