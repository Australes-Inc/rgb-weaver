"""
Main processing pipeline for rgb-weaver
Orchestrates rio-rgbify, mbutil, and TileJSON generation
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import shutil

from tqdm import tqdm

from rgbweaver.metadata import extract_dem_metadata, generate_tilejson, DEMInfo
from rgbweaver.utils import (
    ensure_directory, cleanup_on_error, get_temp_filename,
    RGBWeaverError
)
from rgbweaver.config import (
    DEFAULT_BASE_VAL, DEFAULT_INTERVAL, DEFAULT_ROUND_DIGITS,
    DEFAULT_WORKERS, DEFAULT_FORMAT, DEFAULT_SCHEME,
    DEFAULT_ATTRIBUTION
)

logger = logging.getLogger(__name__)


class PipelineError(RGBWeaverError):
    """Error during pipeline execution."""
    pass


class RGBWeaverPipeline:
    """
    Main processing pipeline for terrain RGB tile generation.
    
    Orchestrates the complete workflow:
    1. Extract DEM metadata
    2. Generate MBTiles with rio-rgbify  
    3. Extract tiles with mbutil
    4. Generate tiles.json
    """
    
    def __init__(
        self,
        input_dem: Path,
        output_dir: Path,
        min_zoom: int,
        max_zoom: int,
        workers: int = DEFAULT_WORKERS,
        format: str = DEFAULT_FORMAT,
        base_val: float = DEFAULT_BASE_VAL,
        interval: float = DEFAULT_INTERVAL,
        round_digits: int = DEFAULT_ROUND_DIGITS,
        scheme: str = DEFAULT_SCHEME,
        name: Optional[str] = None,
        description: Optional[str] = None,
        attribution: str = DEFAULT_ATTRIBUTION,
        force: bool = False,
        **kwargs
    ):
        """
        Initialize pipeline.
        
        Args:
            input_dem: Path to input DEM file
            output_dir: Output directory for tiles and metadata
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
            workers: Number of parallel workers
            format: Output tile format (png, webp)
            base_val: Base value for RGB encoding
            interval: Precision interval for encoding
            round_digits: Number of digits to round
            scheme: Tile naming scheme
            name: Tileset name
            description: Tileset description
            attribution: Attribution string
            force: Force overwrite existing files
            **kwargs: Additional parameters
        """
        self.input_dem = Path(input_dem)
        self.output_dir = Path(output_dir)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.workers = workers
        self.format = format
        self.base_val = base_val
        self.interval = interval
        self.round_digits = round_digits
        self.scheme = scheme
        self.name = name or self.input_dem.stem
        self.description = description
        self.attribution = attribution
        self.force = force
        self.kwargs = kwargs
        
        # Internal state
        self.dem_info: Optional[DEMInfo] = None
        self.temp_dir: Optional[Path] = None
        self.mbtiles_path: Optional[Path] = None
        self.tiles_dir: Optional[Path] = None
        
    def run(self) -> None:
        """
        Execute the complete pipeline.
        
        Raises:
            PipelineError: If any step fails
        """
        logger.info("Starting RGB Weaver pipeline")
        logger.info(f"Input DEM: {self.input_dem}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Zoom range: {self.min_zoom} - {self.max_zoom}")
        
        try:
            # Setup output directory
            self._setup_output_directory()
            
            # Step 1: Extract DEM metadata
            self._extract_metadata()
            
            # Step 2: Generate MBTiles with rio-rgbify
            self._generate_mbtiles()
            
            # Step 3: Extract tiles with mbutil
            self._extract_tiles()
            
            # Step 4: Generate tiles.json
            self._generate_tilejson()
            
            # Step 5: Cleanup
            self._cleanup()
            
            logger.info("Pipeline completed successfully!")
            logger.info(f"Output available at: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self._cleanup_on_error()
            raise PipelineError(f"Pipeline execution failed: {e}")
    
    def _setup_output_directory(self) -> None:
        """Setup the output directory structure."""
        logger.info("Setting up output directory...")
        
        try:
            # Create main output directory
            ensure_directory(self.output_dir, force=self.force)
            
            # Create tiles subdirectory
            self.tiles_dir = self.output_dir / "tiles"
            ensure_directory(self.tiles_dir)
            
            # Create temporary directory for intermediate files
            self.temp_dir = Path(tempfile.mkdtemp(prefix="rgb_weaver_"))
            logger.debug(f"Temporary directory: {self.temp_dir}")
            
        except Exception as e:
            raise PipelineError(f"Failed to setup output directory: {e}")
    
    def _extract_metadata(self) -> None:
        """Extract metadata from input DEM."""
        logger.info("Extracting DEM metadata...")
        
        try:
            self.dem_info = extract_dem_metadata(self.input_dem, compute_stats=True)
            
            # Log key information
            bounds = self.dem_info.bounds_wgs84
            center = self.dem_info.center_wgs84
            logger.info(f"Bounds (WGS84): {bounds}")
            logger.info(f"Center (WGS84): {center}")
            
            if self.dem_info.min_value is not None and self.dem_info.max_value is not None:
                logger.info(f"Value range: {self.dem_info.min_value} to {self.dem_info.max_value}")
            
        except Exception as e:
            raise PipelineError(f"Failed to extract DEM metadata: {e}")
    
    def _generate_mbtiles(self) -> None:
        """Generate MBTiles using rio-rgbify."""
        logger.info("Generating MBTiles with rio-rgbify...")
        
        try:
            # Create temporary MBTiles file
            mbtiles_name = get_temp_filename(self.name, '.mbtiles')
            self.mbtiles_path = self.temp_dir / mbtiles_name
            
            # Build rio rgbify command
            cmd = [
                'rio', 'rgbify',
                str(self.input_dem),
                str(self.mbtiles_path),
                '--min-z', str(self.min_zoom),
                '--max-z', str(self.max_zoom),
                '--workers', str(self.workers),
                '--format', self.format,
                '--base-val', str(self.base_val),
                '--interval', str(self.interval),
                '--round-digits', str(self.round_digits)
            ]
            
            logger.debug(f"Rio-rgbify command: {' '.join(cmd)}")
            
            # Execute with progress tracking
            with tqdm(desc="Generating MBTiles", unit="tiles") as pbar:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    raise PipelineError(f"Rio-rgbify failed: {error_msg}")
                
                pbar.update(1)
            
            # Verify MBTiles file was created
            if not self.mbtiles_path.exists():
                raise PipelineError("MBTiles file was not created")
            
            logger.info(f"MBTiles generated: {self.mbtiles_path}")
            
        except subprocess.SubprocessError as e:
            raise PipelineError(f"Failed to run rio-rgbify: {e}")
        except Exception as e:
            raise PipelineError(f"MBTiles generation failed: {e}")
    
    def _extract_tiles(self) -> None:
        """Extract tiles from MBTiles using mbutil."""
        logger.info("Extracting tiles with mbutil...")
        
        try:
            # Create a temporary extraction directory
            temp_tiles_dir = self.temp_dir / "extracted_tiles"
            
            # Build mbutil command (extract to temp dir first)
            cmd = [
                'mb-util',
                str(self.mbtiles_path),
                str(temp_tiles_dir),
                '--scheme', self.scheme,
                '--image_format', self.format,
                '--silent'
            ]
            
            logger.debug(f"Mbutil command: {' '.join(cmd)}")
            
            # Execute with progress tracking
            with tqdm(desc="Extracting tiles", unit="tiles") as pbar:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    raise PipelineError(f"Mbutil failed: {error_msg}")
                
                pbar.update(1)
            
            # Move extracted tiles to final destination
            if temp_tiles_dir.exists():
                # Remove existing tiles directory if it exists
                if self.tiles_dir.exists():
                    shutil.rmtree(self.tiles_dir)
                
                # Move the extracted tiles
                shutil.move(str(temp_tiles_dir), str(self.tiles_dir))
            else:
                raise PipelineError("No tiles were extracted")
            
            # Count extracted tiles
            tile_count = sum(1 for _ in self.tiles_dir.rglob(f"*.{self.format}"))
            logger.info(f"Extracted {tile_count} tiles")
            
        except subprocess.SubprocessError as e:
            raise PipelineError(f"Failed to run mbutil: {e}")
        except Exception as e:
            raise PipelineError(f"Tile extraction failed: {e}")
    
    def _generate_tilejson(self) -> None:
        """Generate tiles.json metadata file."""
        logger.info("Generating tiles.json...")
        
        try:
            if self.dem_info is None:
                raise PipelineError("DEM metadata not available")
            
            # Determine tile URL template based on scheme
            if self.scheme == "tms":
                tile_template = f"./tiles/{{z}}/{{x}}/{{y}}.{self.format}"
            else:  # xyz and others
                tile_template = f"./tiles/{{z}}/{{x}}/{{y}}.{self.format}"
            
            # Generate tiles.json
            tilejson_path = self.output_dir / "tiles.json"
            
            generate_tilejson(
                dem_info=self.dem_info,
                output_path=tilejson_path,
                name=self.name,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
                format=self.format,
                scheme=self.scheme,
                description=self.description,
                attribution=self.attribution,
                tile_url_template=tile_template,
                **self.kwargs
            )
            
            logger.info(f"TileJSON generated: {tilejson_path}")
            
        except Exception as e:
            raise PipelineError(f"TileJSON generation failed: {e}")
    
    def _cleanup(self) -> None:
        """Clean up temporary files."""
        logger.debug("Cleaning up temporary files...")
        
        try:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")
    
    def _cleanup_on_error(self) -> None:
        """Clean up files on error."""
        logger.debug("Cleaning up after error...")
        
        try:
            # Clean temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Optionally clean output directory if it was created by us
            if self.force and self.output_dir.exists():
                cleanup_on_error(self.output_dir)
                
        except Exception as e:
            logger.warning(f"Failed to clean up after error: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get pipeline execution summary.
        
        Returns:
            Dictionary with execution details
        """
        summary = {
            'input_dem': str(self.input_dem),
            'output_dir': str(self.output_dir),
            'zoom_range': f"{self.min_zoom}-{self.max_zoom}",
            'format': self.format,
            'scheme': self.scheme,
            'name': self.name,
            'workers': self.workers
        }
        
        if self.dem_info:
            summary.update({
                'dem_info': self.dem_info.to_dict(),
                'bounds_wgs84': self.dem_info.bounds_wgs84,
                'center_wgs84': self.dem_info.center_wgs84
            })
        
        return summary