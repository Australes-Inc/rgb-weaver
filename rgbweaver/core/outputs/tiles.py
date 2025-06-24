# rgbweaver/core/outputs/tiles.py
"""
PNG tiles output handler
"""

from pathlib import Path
from ..processors.base import ProcessorBase, ProcessResult


class TilesHandler:
    """Handler for PNG tiles output"""
    
    def handle(self, dem_path: Path, output_path: Path, **kwargs) -> dict:
        """Generate PNG tiles directory from DEM"""
        from ..processors.tiles import TilesProcessor
        
        processor = TilesProcessor()
        result = processor.process(dem_path, output_path, **kwargs)
        
        return {
            'success': result.success,
            'output_path': result.output_path,
            'metadata': result.metadata,
            'error': result.error
        }