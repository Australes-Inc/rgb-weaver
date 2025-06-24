# rgbweaver/core/outputs/pmtiles.py
"""
PMTiles output handler
"""

from pathlib import Path
from ..processors.base import ProcessorBase, ProcessResult


class PMTilesHandler:
    """Handler for PMTiles output"""
    
    def handle(self, dem_path: Path, output_path: Path, **kwargs) -> dict:
        """Generate PMTiles from DEM"""
        from ..processors.pmtiles import PMTilesProcessor
        
        processor = PMTilesProcessor()
        result = processor.process(dem_path, output_path, **kwargs)
        
        return {
            'success': result.success,
            'output_path': result.output_path,
            'metadata': result.metadata,
            'error': result.error
        }
