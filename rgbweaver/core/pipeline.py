# rgbweaver/core/pipeline.py (AMÉLIORÉ PHASE 2)
"""
Enhanced main pipeline orchestrator with Phase 2 improvements
"""

import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..metadata import extract_dem_metadata
from .outputs import OutputFactory, OutputType
from .processors import ProcessorFactory
from ..utils import format_file_size, estimate_processing_time


class TempFileManager:
    """Enhanced context manager for temporary files cleanup"""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dir = None
        self.created_files = []
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="rgbweaver_")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def add_temp_file(self, filepath: str):
        """Add a temporary file to track"""
        self.temp_files.append(filepath)
    
    def get_temp_path(self, suffix: str = "") -> Path:
        """Get a new temporary file path"""
        temp_path = Path(self.temp_dir) / f"temp_{len(self.temp_files)}{suffix}"
        self.add_temp_file(str(temp_path))
        return temp_path
    
    def cleanup(self):
        """Clean up all temporary files and directories"""
        cleaned = 0
        failed = 0
        
        for temp_file in self.temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    if temp_path.is_file():
                        temp_path.unlink()
                        cleaned += 1
                    else:
                        import shutil
                        shutil.rmtree(temp_path)
                        cleaned += 1
            except Exception as e:
                failed += 1
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
        
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not delete temp directory {self.temp_dir}: {e}")
        
        if cleaned > 0:
            print(f"Cleaned up {cleaned} temporary files")


class Pipeline:
    """Enhanced main processing pipeline orchestrator"""
    
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet
        self.start_time = None
    
    def log(self, message: str, level: str = "info"):
        """Log message based on verbosity settings"""
        if self.quiet and level not in ["error", "warning"]:
            return
    
    def process(self, 
                dem_path: str, 
                output_path: str, 
                min_z: int,
                max_z: int,
                tilejson: bool = True,
                **kwargs) -> Dict[str, Any]:
        """
        Enhanced main processing pipeline with better monitoring
        
        Args:
            dem_path: Path to input DEM
            output_path: Path for output
            min_z: Minimum zoom level
            max_z: Maximum zoom level  
            tilejson: Whether to generate TileJSON (for tiles output)
            **kwargs: Additional processing options
            
        Returns:
            Dict with processing results and metadata
        """
        
        self.start_time = time.time()
        
        dem_path = Path(dem_path)
        output_path = Path(output_path)
        
        if not dem_path.exists():
            raise FileNotFoundError(f"DEM file not found: {dem_path}")
        
        self.log("Starting rgb-weaver enhanced pipeline", "step")
        self.log(f"Input DEM: {dem_path}")
        self.log(f"Output: {output_path}")
        
        # Detect output type
        output_type = OutputFactory.detect_output_type(str(output_path), tilejson)
        self.log(f"Detected output type: {output_type.value}")
        
        # Show processing estimate
        zoom_range = max_z - min_z + 1
        workers = kwargs.get('workers', 4)
        estimated_time = estimate_processing_time(zoom_range, workers)
        self.log(f"Estimated processing time: {estimated_time}")
        
        # Extract DEM metadata
        self.log("Extracting DEM metadata...", "step")
        try:
            dem_metadata = extract_dem_metadata(str(dem_path))
            self.log(f"DEM bounds: {dem_metadata.bounds_wgs84}")
            self.log(f"DEM CRS: {dem_metadata.crs}")
            
            # Calculate DEM area for additional context
            bounds = dem_metadata.bounds_wgs84
            area_deg = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
            self.log(f"Coverage area: {area_deg:.4f} square degrees")
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract DEM metadata: {e}")
        
        # Validate zoom range
        if max_z < min_z:
            raise ValueError(f"max_z ({max_z}) must be >= min_z ({min_z})")
        
        if zoom_range > 10:
            self.log(f"Large zoom range ({zoom_range} levels) detected - this may take significant time", "warning")
        
        # Process with temporary file management
        with TempFileManager() as temp_manager:
            try:
                # Create processor based on output type
                processor = ProcessorFactory.create_processor(output_type)
                processor_name = processor.__class__.__name__
                
                self.log(f"Processing with {processor_name}...", "step")
                
                # Prepare processing arguments
                process_kwargs = {
                    'min_z': min_z,
                    'max_z': max_z,
                    'tilejson': tilejson,
                    'dem_metadata': dem_metadata,
                    'temp_manager': temp_manager,
                    'verbose': self.verbose,
                    **kwargs
                }
                
                # Show processing details
                if self.verbose:
                    self.log(f"Processing parameters:")
                    self.log(f"   • Zoom range: {min_z}-{max_z} ({zoom_range} levels)")
                    self.log(f"   • Workers: {kwargs.get('workers', 4)}")
                    self.log(f"   • Format: {kwargs.get('format', 'png')}")
                    self.log(f"   • Base value: {kwargs.get('base_val', -10000)}")
                    self.log(f"   • Interval: {kwargs.get('interval', 0.1)}")
                
                # Execute processing with timing
                processing_start = time.time()
                result = processor.process(dem_path, output_path, **process_kwargs)
                processing_time = time.time() - processing_start
                
                if not result.success:
                    raise RuntimeError(f"Processing failed: {result.error}")
                
                # Success logging with details
                self.log(f"Successfully generated {output_type.value}: {result.output_path}", "success")
                self.log(f"Processing completed in {processing_time:.1f} seconds")
                
                # Show output statistics
                metadata = result.metadata or {}
                self._log_output_statistics(metadata, output_type)
                
                # Calculate total time
                total_time = time.time() - self.start_time
                self.log(f"Total pipeline time: {total_time:.1f} seconds", "success")
                
                return {
                    'success': True,
                    'output_type': output_type.value,
                    'output_path': str(result.output_path),
                    'metadata': metadata,
                    'dem_metadata': dem_metadata.__dict__,
                    'processing_time_seconds': processing_time,
                    'total_time_seconds': total_time,
                    'zoom_range': zoom_range
                }
                
            except Exception as e:
                self.log(f"Pipeline failed: {e}", "error")
                raise
    
    def _log_output_statistics(self, metadata: Dict[str, Any], output_type: OutputType):
        """Log detailed output statistics based on format"""
        
        if not metadata:
            return
        
        # Common statistics
        if 'file_size_bytes' in metadata:
            size_str = format_file_size(metadata['file_size_bytes'])
            self.log(f"File size: {size_str}")
        
        if 'total_size_bytes' in metadata:
            size_str = format_file_size(metadata['total_size_bytes'])
            self.log(f"Total size: {size_str}")
        
        # Format-specific statistics
        if output_type == OutputType.MBTILES:
            self._log_mbtiles_stats(metadata)
        elif output_type == OutputType.PMTILES:
            self._log_pmtiles_stats(metadata)
        elif output_type in [OutputType.TILES, OutputType.TILES_WITH_JSON]:
            self._log_tiles_stats(metadata)
    
    def _log_mbtiles_stats(self, metadata: Dict[str, Any]):
        """Log MBTiles specific statistics"""
        if 'estimated_tiles' in metadata:
            self.log(f"Estimated tiles: {metadata['estimated_tiles']:,}")
        
        if 'encoding_params' in metadata:
            params = metadata['encoding_params']
            self.log(f"Encoding: base={params.get('base_val')}, interval={params.get('interval')}")
    
    def _log_pmtiles_stats(self, metadata: Dict[str, Any]):
        """Log PMTiles specific statistics"""
        if 'temp_mbtiles_size' in metadata and 'file_size_bytes' in metadata:
            temp_size = metadata['temp_mbtiles_size']
            final_size = metadata['file_size_bytes']
            if temp_size > 0:
                compression_ratio = (1 - final_size / temp_size) * 100
                self.log(f"PMTiles compression: {compression_ratio:.1f}% size reduction")
    
    def _log_tiles_stats(self, metadata: Dict[str, Any]):
        """Log PNG tiles specific statistics"""
        if 'total_tiles' in metadata:
            self.log(f"Total tiles generated: {metadata['total_tiles']:,}")
        
        if 'tiles_per_zoom' in metadata:
            tiles_per_zoom = metadata['tiles_per_zoom']
            self.log("Tiles per zoom level:")
            for zoom in sorted(tiles_per_zoom.keys()):
                count = tiles_per_zoom[zoom]
                self.log(f"   • Z{zoom}: {count:,} tiles")
        
        if 'avg_tile_size_bytes' in metadata:
            avg_size = format_file_size(metadata['avg_tile_size_bytes'])
            self.log(f"Average tile size: {avg_size}")
        
        if 'tilejson_generated' in metadata and metadata['tilejson_generated']:
            tilejson_path = metadata.get('tilejson_path')
            self.log(f"TileJSON generated: {tilejson_path}")