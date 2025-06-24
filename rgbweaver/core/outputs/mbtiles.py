# rgbweaver/core/outputs/mbtiles.py
"""
MBTiles output handler
"""

from pathlib import Path
from ..processors.base import ProcessorBase, ProcessResult
from ...utils import run_command


class MBTilesHandler:
    """Handler for MBTiles output"""
    
    def handle(self, dem_path: Path, output_path: Path, **kwargs) -> dict:
        """Generate MBTiles directly from DEM"""
        from ..processors.mbtiles import MBTilesProcessor
        
        processor = MBTilesProcessor()
        result = processor.process(dem_path, output_path, **kwargs)
        
        return {
            'success': result.success,
            'output_path': result.output_path,
            'metadata': result.metadata,
            'error': result.error
        }