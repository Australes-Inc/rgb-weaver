"""
Processor factory for creating appropriate processors
"""

from pathlib import Path
from ..outputs import OutputType
from .base import ProcessorBase


class ProcessorFactory:
    """Factory for creating appropriate processors based on output type"""
    
    @staticmethod
    def create_processor(output_type: OutputType) -> ProcessorBase:
        """Create appropriate processor for output type"""
        from .mbtiles import MBTilesProcessor
        from .pmtiles import PMTilesProcessor
        from .tiles import TilesProcessor
        
        processors = {
            OutputType.MBTILES: MBTilesProcessor,
            OutputType.PMTILES: PMTilesProcessor,
            OutputType.TILES: TilesProcessor,
            OutputType.TILES_WITH_JSON: TilesProcessor
        }
        
        processor_class = processors.get(output_type)
        if not processor_class:
            raise ValueError(f"No processor available for output type: {output_type}")
        
        return processor_class()