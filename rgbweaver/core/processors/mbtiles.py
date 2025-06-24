# rgbweaver/core/processors/mbtiles.py
"""
MBTiles processor - generates MBTiles directly from DEM using rio-rgbify
"""

from pathlib import Path
from .base import ProcessorBase, ProcessResult
from ...utils import run_command


class MBTilesProcessor(ProcessorBase):
    """
    Processor for direct MBTiles generation using rio-rgbify
    
    Workflow: DEM → MBTiles (rio rgbify)
    """
    
    def process(self, dem_path: Path, output_path: Path, **kwargs) -> ProcessResult:
        """
        Process DEM directly to MBTiles using rio-rgbify
        
        Args:
            dem_path: Input DEM path
            output_path: Output MBTiles path (.mbtiles)
            **kwargs: Processing options
            
        Returns:
            ProcessResult with success status and metadata
        """
        verbose = kwargs.get('verbose', False)
        
        try:
            if verbose:
                print("Generating MBTiles using rio-rgbify...")
            
            # Extract processing parameters with defaults
            min_z = kwargs.get('min_z', 8)
            max_z = kwargs.get('max_z', 14)
            base_val = kwargs.get('base_val', -10000)
            interval = kwargs.get('interval', 0.1)
            round_digits = kwargs.get('round_digits', 0)
            workers = kwargs.get('workers', 4)
            format_type = kwargs.get('format', 'png')
            
            # Validate zoom range
            if max_z < min_z:
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error=f"Invalid zoom range: max_z ({max_z}) < min_z ({min_z})"
                )
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build rio rgbify command
            cmd = [
                'rio', 'rgbify',
                str(dem_path),
                str(output_path),
                '--min-z', str(min_z),
                '--max-z', str(max_z),
                '--base-val', str(base_val),
                '--interval', str(interval),
                '--round-digits', str(round_digits),
                '--workers', str(workers),
                '--format', format_type
            ]
            
            if verbose:
                cmd.append('--verbose')
            
            # Execute rio-rgbify
            result = run_command(cmd, verbose=verbose)
            
            if verbose:
                print("MBTiles generation completed")
            
            # Verify output file was created
            if not output_path.exists():
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error="MBTiles file was not created"
                )
            
            # Get file size and calculate tile count estimate
            file_size = output_path.stat().st_size
            
            # Rough tile count estimate (simplified calculation)
            zoom_levels = max_z - min_z + 1
            estimated_tiles = sum(4**z for z in range(zoom_levels))
            
            metadata = {
                'format': 'mbtiles',
                'tile_format': format_type,
                'min_zoom': min_z,
                'max_zoom': max_z,
                'zoom_levels': zoom_levels,
                'encoding_params': {
                    'base_val': base_val,
                    'interval': interval,
                    'round_digits': round_digits
                },
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'workers_used': workers,
                'estimated_tiles': estimated_tiles,
                'processing_tool': 'rio-rgbify'
            }
            
            return ProcessResult(
                success=True,
                output_path=output_path,
                metadata=metadata,
                temp_files=[]
            )
            
        except Exception as e:
            return ProcessResult(
                success=False,
                output_path=output_path,
                error=f"MBTiles generation failed: {str(e)}"
            )