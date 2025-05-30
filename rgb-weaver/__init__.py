"""
rgb-weaver: Generate terrain RGB raster tiles directly from a DEM

This package automates the creation of terrain RGB tiles by orchestrating:
- rio-rgbify for RGB encoding
- mbutil for tile extraction  
- GDAL for metadata extraction
- TileJSON generation
"""

__version__ = '0.1.0'
__author__ = 'Australes Inc'
__email__ = 'diegoposba@gmail.com'
__description__ = 'Generate terrain RGB raster tiles directly from a DEM'

from rgbweaver.pipeline import RGBWeaverPipeline
from rgbweaver.metadata import DEMMetadata, TileJSONGenerator

__all__ = [
    'RGBWeaverPipeline',
    'DEMMetadata', 
    'TileJSONGenerator',
]