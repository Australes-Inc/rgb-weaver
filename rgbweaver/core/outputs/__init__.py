# rgbweaver/core/outputs/__init__.py
"""
Output type definitions and factory
"""

from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class OutputType(Enum):
    """Supported output types with PMTiles integration"""
    MBTILES = "mbtiles"
    PMTILES = "pmtiles" 
    TILES = "tiles"
    TILES_WITH_JSON = "tiles_with_json"
    
    def __str__(self):
        return self.value
    
    @property
    def description(self):
        """Human-readable description of output type"""
        descriptions = {
            self.MBTILES: "MBTiles database file (.mbtiles)",
            self.PMTILES: "PMTiles archive file (.pmtiles)", 
            self.TILES: "PNG/WebP tiles directory without metadata",
            self.TILES_WITH_JSON: "PNG/WebP tiles directory with TileJSON metadata"
        }
        return descriptions[self]
    
    @property
    def file_extension(self):
        """File extension for this output type"""
        extensions = {
            self.MBTILES: ".mbtiles",
            self.PMTILES: ".pmtiles",
            self.TILES: None,  
            self.TILES_WITH_JSON: None  
        }
        return extensions[self]


@runtime_checkable
class OutputHandler(Protocol):
    """Protocol for output handlers"""
    
    def handle(self, dem_path: Path, output_path: Path, **kwargs) -> dict:
        """Process DEM to specified output format"""
        ...


class OutputFactory:
    """Enhanced factory for creating appropriate output handlers"""
    
    @staticmethod
    def detect_output_type(output_path: str, tilejson: bool = True) -> OutputType:
        """
        Detect output type from path and options with validation
        
        Args:
            output_path: Output path (file or directory)
            tilejson: Whether to generate TileJSON (for directory outputs)
            
        Returns:
            OutputType enum value
            
        Raises:
            ValueError: If output path format is invalid
        """
        path = Path(output_path)
        suffix = path.suffix.lower()
        
        if suffix == '.mbtiles':
            return OutputType.MBTILES
        elif suffix == '.pmtiles':
            return OutputType.PMTILES
        elif suffix == '':
            # Directory output
            if tilejson:
                return OutputType.TILES_WITH_JSON
            else:
                return OutputType.TILES
        else:
            # Invalid file extension
            raise ValueError(
                f"Unsupported output format: '{suffix}'\n"
                f"Supported formats:\n"
                f"  • .mbtiles - MBTiles database\n"
                f"  • .pmtiles - PMTiles archive\n"
                f"  • directory/ - PNG/WebP tiles"
            )
    
    @staticmethod
    def create_handler(output_type: OutputType) -> OutputHandler:
        """
        Create appropriate output handler with error handling
        
        Args:
            output_type: Type of output to create handler for
            
        Returns:
            OutputHandler instance
            
        Raises:
            ValueError: If output type is not supported
            RuntimeError: If handler cannot be created (e.g., missing dependencies)
        """
        try:
            if output_type == OutputType.MBTILES:
                from .mbtiles import MBTilesHandler
                return MBTilesHandler()
            
            elif output_type == OutputType.PMTILES:
                from .pmtiles import PMTilesHandler
                return PMTilesHandler()
            
            elif output_type in [OutputType.TILES, OutputType.TILES_WITH_JSON]:
                from .tiles import TilesHandler
                return TilesHandler()
            
            else:
                raise ValueError(f"Unsupported output type: {output_type}")
                
        except ImportError as e:
            raise RuntimeError(
                f"Cannot create handler for {output_type}: {e}\n"
                f"This may indicate missing dependencies."
            ) from e
    
    @staticmethod
    def get_supported_types() -> list[OutputType]:
        """Get list of supported output types on current platform"""
        supported = [OutputType.MBTILES, OutputType.TILES, OutputType.TILES_WITH_JSON]
        
        # Check if PMTiles is available on current platform
        try:
            from ..processors.pmtiles import PMTilesProcessor
            PMTilesProcessor()  # Try to initialize
            supported.append(OutputType.PMTILES)
        except Exception:
            pass  # PMTiles not available on this platform
        
        return supported