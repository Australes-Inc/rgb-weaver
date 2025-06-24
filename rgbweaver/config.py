# rgbweaver/config.py (mise à jour)
"""
Configuration constants and defaults for rgb-weaver v2.0.0
"""

from enum import Enum
from typing import Dict, Any


class DefaultValues:
    """Default values for rgb-weaver processing"""
    
    # Zoom levels
    MIN_ZOOM = 0
    MAX_ZOOM = 22
    DEFAULT_MIN_ZOOM = 8
    DEFAULT_MAX_ZOOM = 14
    
    # RGB encoding
    BASE_VAL = -10000
    INTERVAL = 0.1
    ROUND_DIGITS = 0
    
    # Processing
    WORKERS = 4
    FORMAT = 'png'
    SCHEME = 'xyz'
    
    # TileJSON
    TILEJSON_VERSION = "3.0.0"
    TILE_SIZE = 512
    
    # File extensions
    SUPPORTED_DEM_EXTENSIONS = {
        '.tif', '.tiff', '.img', '.bil', '.bip', '.bsq', 
        '.asc', '.dem', '.hgt', '.dt0', '.dt1', '.dt2', '.vrt'
    }
    
    SUPPORTED_OUTPUT_EXTENSIONS = {
        '.mbtiles', '.pmtiles'
    }


class OutputFormats:
    """Supported output formats"""
    
    TILE_FORMATS = ['png', 'webp']
    SCHEMES = ['xyz', 'tms', 'zyx', 'wms']
    
    # Format-specific settings
    FORMAT_SETTINGS = {
        'png': {
            'mime_type': 'image/png',
            'extension': 'png',
            'compression': 'lossless'
        },
        'webp': {
            'mime_type': 'image/webp', 
            'extension': 'webp',
            'compression': 'lossless'
        }
    }


class ValidationRules:
    """Validation rules and limits"""
    
    # Zoom level validation
    ZOOM_RANGE_WARNING_THRESHOLD = 10  # Warn if range > 10 levels
    MAX_SAFE_ZOOM_RANGE = 15          # Hard limit for safety
    
    # File size warnings (in MB)
    LARGE_OUTPUT_WARNING_SIZE = 500
    VERY_LARGE_OUTPUT_WARNING_SIZE = 2000
    
    # Memory and performance
    MAX_WORKERS = 16
    RECOMMENDED_WORKERS = 8


class ErrorMessages:
    """Standard error messages"""
    
    DEPENDENCY_MISSING = "Required dependency '{dependency}' not found. Please install: {install_cmd}"
    INVALID_ZOOM_RANGE = "Invalid zoom range: min_z ({min_z}) must be <= max_z ({max_z})"
    ZOOM_OUT_OF_BOUNDS = "Zoom level {zoom} is out of bounds (must be 0-22)"
    LARGE_ZOOM_RANGE = "Warning: Large zoom range ({range} levels) will generate many tiles"
    FILE_NOT_FOUND = "File not found: {filepath}"
    OUTPUT_EXISTS = "Output already exists: {output}. Use --force to overwrite"
    UNSUPPORTED_FORMAT = "Unsupported format: {format}. Supported: {supported}"
    
    # Processing errors
    PROCESSING_FAILED = "Processing failed: {error}"
    TEMP_CLEANUP_FAILED = "Warning: Could not clean up temporary file: {filepath}"
    CONVERSION_FAILED = "Conversion failed from {source_format} to {target_format}: {error}"


class LogMessages:
    """Standard log messages"""
    
    STARTING_PIPELINE = "Starting rgb-weaver pipeline"
    DETECTING_OUTPUT_TYPE = "Detected output type: {output_type}"
    EXTRACTING_METADATA = "Extracting DEM metadata..."
    PROCESSING_WITH = "Processing with {processor_name}..."
    CONVERTING_FORMAT = "Converting {source} to {target}..."
    GENERATING_TILES = "Generating tiles from MBTiles..."
    GENERATING_TILEJSON = "Generating TileJSON metadata..."
    SUCCESS = "Successfully generated {output_type}: {output_path}"
    CLEANUP_TEMP = "Cleaning up temporary files..."


# Configuration for external tools
EXTERNAL_TOOLS = {
    'rio': {
        'command': 'rio',
        'check_arg': '--help',
        'install_cmd': 'pip install rasterio[s3]',
        'description': 'Rasterio CLI'
    },
    'mb-util': {
        'command': 'mb-util', 
        'check_arg': '--help',
        'install_cmd': 'pip install git+https://github.com/Australes-Inc/mbutil.git',
        'description': 'MBUtil (enhanced)'
    },
    'pmtiles': {
        'command': 'pmtiles',
        'check_arg': '--help', 
        'install_cmd': 'Download from https://github.com/protomaps/go-pmtiles/releases',
        'description': 'go-pmtiles'
    }
}