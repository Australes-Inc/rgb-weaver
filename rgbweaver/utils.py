"""
Utility functions for rgb-weaver
"""

import os
import logging
from pathlib import Path
from typing import Union

import rasterio
from rasterio.errors import RasterioIOError

from rgbweaver.config import (
    SUPPORTED_RASTER_FORMATS, MAX_FILE_SIZE_MB,
    MIN_ZOOM_LEVEL, MAX_ZOOM_LEVEL
)

logger = logging.getLogger(__name__)


class RGBWeaverError(Exception):
    """Base exception for rgb-weaver."""
    pass


class ValidationError(RGBWeaverError):
    """Input parameter validation error."""
    pass


def validate_input_file(filepath: Path) -> None:
    """
    Validate that the input file is usable.
    
    Args:
        filepath: Path to file to validate
        
    Raises:
        ValidationError: If file is not valid
    """
    logger.debug(f"Validating input file: {filepath}")
    
    # Check existence
    if not filepath.exists():
        raise ValidationError(f"File '{filepath}' does not exist")
    
    # Check that it's a file
    if not filepath.is_file():
        raise ValidationError(f"'{filepath}' is not a file")
    
    # Check extension
    suffix = filepath.suffix.lower()
    if suffix not in SUPPORTED_RASTER_FORMATS:
        supported_str = ', '.join(SUPPORTED_RASTER_FORMATS)
        raise ValidationError(
            f"Format '{suffix}' not supported. "
            f"Supported formats: {supported_str}"
        )
    
    # Check file size
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValidationError(
            f"File too large ({file_size_mb:.1f} MB). "
            f"Limit: {MAX_FILE_SIZE_MB} MB"
        )
    
    # Check that file can be opened with rasterio
    try:
        with rasterio.open(filepath) as src:
            # Basic checks
            if src.count == 0:
                raise ValidationError("File contains no bands")
            
            if src.width == 0 or src.height == 0:
                raise ValidationError("File has invalid dimensions")
            
            # Check CRS
            if src.crs is None:
                logger.warning("  File has no coordinate reference system defined")
            
            logger.debug(
                f"Valid file: {src.width}x{src.height}, "
                f"{src.count} band(s), CRS: {src.crs}"
            )
            
    except RasterioIOError as e:
        raise ValidationError(f"Cannot read raster file: {e}")
    except Exception as e:
        raise ValidationError(f"Error opening file: {e}")


def validate_zoom_levels(min_z: int, max_z: int) -> None:
    """
    Validate zoom levels.
    
    Args:
        min_z: Minimum zoom level
        max_z: Maximum zoom level
        
    Raises:
        ValidationError: If zoom levels are invalid
    """
    logger.debug(f"Validating zoom levels: {min_z} - {max_z}")
    
    # Check absolute limits
    if min_z < MIN_ZOOM_LEVEL:
        raise ValidationError(
            f"Minimum zoom ({min_z}) below limit ({MIN_ZOOM_LEVEL})"
        )
    
    if max_z > MAX_ZOOM_LEVEL:
        raise ValidationError(
            f"Maximum zoom ({max_z}) above limit ({MAX_ZOOM_LEVEL})"
        )
    
    # Check consistency
    if min_z > max_z:
        raise ValidationError(
            f"Minimum zoom ({min_z}) greater than maximum zoom ({max_z})"
        )
    
    # Warning if too many levels
    zoom_range = max_z - min_z + 1
    if zoom_range > 10:
        logger.warning(
            f"  Large zoom range ({zoom_range} levels). "
            "Processing may take very long."
        )


def ensure_directory(path: Union[str, Path], force: bool = False) -> Path:
    """
    Ensure a directory exists, create if necessary.
    
    Args:
        path: Directory path
        force: If True, clear existing content
        
    Returns:
        Path: Created directory path
        
    Raises:
        ValidationError: If directory cannot be created
    """
    path = Path(path)
    
    if path.exists():
        if not path.is_dir():
            raise ValidationError(f"'{path}' exists but is not a directory")
        
        if force:
            logger.debug(f"Cleaning existing directory: {path}")
            import shutil
            shutil.rmtree(path)
            path.mkdir(parents=True)
    else:
        logger.debug(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
    
    return path


def cleanup_on_error(path: Path) -> None:
    """
    Clean up temporary files on error.
    
    Args:
        path: Directory to clean
    """
    if path.exists() and path.is_dir():
        logger.debug(f"Cleaning temporary files: {path}")
        import shutil
        try:
            shutil.rmtree(path)
        except Exception as e:
            logger.warning(f"Cannot clean {path}: {e}")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in readable units.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g. "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_temp_filename(base_name: str, suffix: str = '.tmp') -> str:
    """
    Generate unique temporary filename.
    
    Args:
        base_name: Base name
        suffix: File suffix
        
    Returns:
        str: Temporary filename
    """
    import tempfile
    import uuid
    
    safe_name = "".join(c for c in base_name if c.isalnum() or c in '-_.')
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{safe_name}_{unique_id}{suffix}"