# rgbweaver/__init__.py (VERSION FINALE)
"""
rgb-weaver: Enhanced terrain RGB raster tile generator

Generate terrain RGB tiles from DEMs with multiple output formats:
- PMTiles (.pmtiles) - Modern web-optimized format
- MBTiles (.mbtiles) - SQLite-based format for offline use  
- PNG/WebP tiles - Directory structure with optional TileJSON

Features:
- Cross-platform support (Windows, Linux, macOS Intel)
- Bundled PMTiles binary (no external dependencies)
- Multiple tile formats (PNG, WebP)
- Flexible RGB encoding parameters
- Parallel processing
- Comprehensive metadata generation
"""

__version__ = "2.0.0"
__author__ = "Australes Inc"
__email__ = "diegoposba@gmail.com"
__license__ = "MIT"

# Core exports
from .core import Pipeline, OutputType
from .metadata import extract_dem_metadata, generate_tilejson

# Utility exports  
from .utils import check_dependencies, validate_zoom_levels, format_file_size

__all__ = [
    # Core functionality
    'Pipeline',
    'OutputType', 
    'extract_dem_metadata',
    'generate_tilejson',
    
    # Utilities
    'check_dependencies',
    'validate_zoom_levels', 
    'format_file_size',
    
    # Package info
    '__version__',
    '__author__',
    '__email__',
    '__license__'
]