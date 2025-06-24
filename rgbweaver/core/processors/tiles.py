# rgbweaver/core/processors/tiles.py
"""
PNG tiles processor - generates PNG tiles directory from DEM via MBTiles
"""

import json
from pathlib import Path
from .base import ProcessorBase, ProcessResult
from .mbtiles import MBTilesProcessor
from ...utils import run_command
from ...metadata import generate_tilejson


class TilesProcessor(ProcessorBase):
    """
    Processor for PNG tiles generation
    
    Workflow: DEM → MBTiles (temp) → PNG tiles (mb-util) [+ TileJSON optionnel]
    """
    
    def process(self, dem_path: Path, output_path: Path, **kwargs) -> ProcessResult:
        """
        Process DEM to PNG tiles directory
        
        Args:
            dem_path: Input DEM path
            output_path: Output directory path
            **kwargs: Processing options (including tilejson flag)
            
        Returns:
            ProcessResult with success status and metadata
        """
        temp_manager = kwargs.get('temp_manager')
        tilejson = kwargs.get('tilejson', True)
        verbose = kwargs.get('verbose', False)
        scheme = kwargs.get('scheme', 'xyz')
        format_type = kwargs.get('format', 'png')
        
        if not temp_manager:
            return ProcessResult(
                success=False,
                output_path=output_path,
                error="temp_manager required for tiles processing"
            )
        
        temp_files = []
        
        try:
            if verbose:
                print("Step 1/3: Generating temporary MBTiles...")
            
            # Step 1: Generate temporary MBTiles
            temp_mbtiles = temp_manager.get_temp_path('.mbtiles')
            temp_files.append(str(temp_mbtiles))
            
            # Use MBTiles processor for initial generation
            mbtiles_processor = MBTilesProcessor()
            mbtiles_result = mbtiles_processor.process(dem_path, temp_mbtiles, **kwargs)
            
            if not mbtiles_result.success:
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error=f"MBTiles generation failed: {mbtiles_result.error}",
                    temp_files=temp_files
                )
            
            if verbose:
                print("Step 2/3: Extracting tiles from MBTiles...")
            
            # Step 2: Extract tiles from MBTiles using mb-util
            output_path.mkdir(parents=True, exist_ok=True)
            tiles_dir = output_path / 'tiles'
            
            # Build mb-util command
            cmd = [
                'mb-util',
                str(temp_mbtiles),
                str(tiles_dir),
                '--scheme', scheme,
                '--image_format', format_type
            ]
            
            if not verbose:
                cmd.append('--silent')
            
            # Execute mb-util
            result = run_command(cmd, verbose=verbose)
            
            if verbose:
                print("Tiles extraction completed")
            
            # Verify tiles directory was created
            if not tiles_dir.exists():
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error="Tiles directory was not created",
                    temp_files=temp_files
                )
            
            # Step 3: Generate TileJSON if requested
            tilejson_path = None
            tilejson_data = None
            
            if tilejson:
                if verbose:
                    print("Step 3/3: Generating TileJSON metadata...")
                
                dem_metadata = kwargs.get('dem_metadata')
                if dem_metadata:
                    min_z = kwargs.get('min_z', 8)
                    max_z = kwargs.get('max_z', 14)
                    base_url = kwargs.get('base_url', '')
                    name = kwargs.get('name', dem_path.stem)
                    
                    # Generate TileJSON
                    tilejson_data = generate_tilejson(
                        bounds=dem_metadata.bounds_wgs84,
                        min_zoom=min_z,
                        max_zoom=max_z,
                        tile_format=format_type,
                        base_url=base_url,
                        name=name,
                        description=kwargs.get('description', f'Terrain RGB tiles generated from {dem_path.name}'),
                        attribution=kwargs.get('attribution', ''),
                        scheme=scheme
                    )
                    
                    # Save TileJSON
                    tilejson_path = output_path / 'tiles.json'
                    with open(tilejson_path, 'w', encoding='utf-8') as f:
                        json.dump(tilejson_data, f, indent=2, ensure_ascii=False)
                    
                    if verbose:
                        print("TileJSON metadata generated")
            
            # Calculate statistics
            if verbose:
                print("Calculating tile statistics...")
            
            tile_files = list(tiles_dir.rglob(f'*.{format_type}'))
            total_tiles = len(tile_files)
            total_size = sum(f.stat().st_size for f in tile_files)
            
            # Calculate tiles per zoom level
            tiles_per_zoom = {}
            for tile_file in tile_files:
                # Extract zoom from path: tiles/z/x/y.format
                try:
                    parts = tile_file.relative_to(tiles_dir).parts
                    if len(parts) >= 3:
                        zoom = int(parts[0])
                        tiles_per_zoom[zoom] = tiles_per_zoom.get(zoom, 0) + 1
                except (ValueError, IndexError):
                    pass
            
            # Combine metadata from MBTiles step
            metadata = mbtiles_result.metadata.copy() if mbtiles_result.metadata else {}
            metadata.update({
                'format': 'tiles',
                'tiles_directory': str(tiles_dir),
                'tilejson_generated': tilejson,
                'tilejson_path': str(tilejson_path) if tilejson_path else None,
                'tilejson_data': tilejson_data,
                'scheme': scheme,
                'total_tiles': total_tiles,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'tiles_per_zoom': tiles_per_zoom,
                'avg_tile_size_bytes': round(total_size / total_tiles) if total_tiles > 0 else 0
            })
            
            if verbose:
                print(f"Generated {total_tiles} tiles ({metadata['total_size_mb']} MB)")
            
            return ProcessResult(
                success=True,
                output_path=output_path,
                metadata=metadata,
                temp_files=temp_files
            )
            
        except Exception as e:
            return ProcessResult(
                success=False,
                output_path=output_path,
                error=f"Tiles processing failed: {str(e)}",
                temp_files=temp_files
            )
