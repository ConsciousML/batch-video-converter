import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List

class VideoConfig(BaseModel):
    codec: str = Field(..., description="Video codec to use")
    crf: int = Field(..., ge=0, le=51, description="Constant Rate Factor (0-51)")
    pixel_format: str = Field(..., description="Pixel format")
    tag: str = Field(..., description="Video tag")

class AudioConfig(BaseModel):
    codec: str = Field(..., description="Audio codec to use")
    bitrate: str = Field(..., description="Audio bitrate")

class ProcessingConfig(BaseModel):
    overwrite_output: bool = Field(..., description="Whether to overwrite existing output files")

class LoggingConfig(BaseModel):
    level: str = Field(..., description="Logging level (DEBUG, INFO, WARNING, ERROR)")

class FileConfig(BaseModel):
    input_extensions: List[str] = Field(..., description="List of input file extensions to process")
    ignore: List[str] = Field(default=[], description="List of regex patterns for files/folders to ignore")

class Config(BaseModel):
    video: VideoConfig
    audio: AudioConfig
    processing: ProcessingConfig
    logging: LoggingConfig
    files: FileConfig

def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file with Pydantic validation.
    
    Args:
        config_path: Path to config file. If None, defaults to ./config.yml
        
    Returns:
        Validated Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        pydantic.ValidationError: If config values are invalid
    """
    if config_path is None:
        config_path = Path("config.yml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Pydantic will automatically validate the data
        config = Config(**config_data)
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")