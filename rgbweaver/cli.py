#!/usr/bin/env python
"""
rgb-weaver CLI - Command line interface for terrain RGB tile generation
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

from rgbweaver.config import (
    DEFAULT_BASE_VAL, DEFAULT_INTERVAL, DEFAULT_ROUND_DIGITS,
    DEFAULT_WORKERS, DEFAULT_FORMAT, DEFAULT_SCHEME,
    DEFAULT_ATTRIBUTION, MIN_ZOOM_LEVEL, MAX_ZOOM_LEVEL,
    LOG_FORMAT, LOG_DATE_FORMAT
)
from rgbweaver.pipeline import RGBWeaverPipeline
from rgbweaver.utils import validate_input_file, validate_zoom_levels


def setup_logging(verbose: bool = False, quiet: bool = False):
    """Configure logging according to verbosity level."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )


@click.command()
@click.argument('input_dem', type=click.Path(exists=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option(
    '--min-z', 
    type=int, 
    required=True,
    help=f'Minimum zoom level ({MIN_ZOOM_LEVEL}-{MAX_ZOOM_LEVEL})'
)
@click.option(
    '--max-z', 
    type=int, 
    required=True,
    help=f'Maximum zoom level ({MIN_ZOOM_LEVEL}-{MAX_ZOOM_LEVEL})'
)
@click.option(
    '--workers', '-j',
    type=int,
    default=DEFAULT_WORKERS,
    help=f'Number of parallel workers [default: {DEFAULT_WORKERS}]'
)
@click.option(
    '--format',
    type=click.Choice(['png', 'webp']),
    default=DEFAULT_FORMAT,
    help=f'Output tile format [default: {DEFAULT_FORMAT}]'
)
@click.option(
    '--base-val', '-b',
    type=float,
    default=DEFAULT_BASE_VAL,
    help=f'Base value for RGB encoding [default: {DEFAULT_BASE_VAL}]'
)
@click.option(
    '--interval', '-i',
    type=float,
    default=DEFAULT_INTERVAL,
    help=f'Precision interval for encoding [default: {DEFAULT_INTERVAL}]'
)
@click.option(
    '--round-digits', '-r',
    type=int,
    default=DEFAULT_ROUND_DIGITS,
    help=f'Number of digits to round [default: {DEFAULT_ROUND_DIGITS}]'
)
@click.option(
    '--scheme',
    type=click.Choice(['xyz', 'tms', 'zyx', 'wms']),
    default=DEFAULT_SCHEME,
    help=f'Tile naming scheme [default: {DEFAULT_SCHEME}]'
)
@click.option(
    '--name',
    type=str,
    default=None,
    help='Tileset name (default: DEM filename)'
)
@click.option(
    '--description',
    type=str,
    default=None,
    help='Tileset description'
)
@click.option(
    '--attribution',
    type=str,
    default=DEFAULT_ATTRIBUTION,
    help=f'Attribution to display [default: "{DEFAULT_ATTRIBUTION}"]'
)
@click.option(
    '--base-url',
    type=str,
    default=None,
    help='Base URL for tile server (e.g. http://localhost:3000/assets/)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose mode (show more details)'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Quiet mode (show only errors)'
)
@click.option(
    '--force', '-f',
    is_flag=True,
    help='Force overwrite output directory if it exists'
)
@click.version_option(version='0.1.0', message='%(prog)s version %(version)s')
def main(
    input_dem: Path,
    output_dir: Path,
    min_z: int,
    max_z: int,
    workers: int,
    format: str,
    base_val: float,
    interval: float,
    round_digits: int,
    scheme: str,
    name: Optional[str],
    description: Optional[str],
    attribution: str,
    base_url: Optional[str],
    verbose: bool,
    quiet: bool,
    force: bool
):
    """
    rgb-weaver - Terrain RGB tile generator
    
    Generate terrain RGB tiles directly from a DEM using rio-rgbify, mbutil 
    and GDAL to create a complete tileset with metadata.
    
    INPUT_DEM   : Path to DEM file (GeoTIFF recommended)
    OUTPUT_DIR  : Output directory for tiles and tiles.json
    
    Examples:
    
        # Basic usage
        rgb-weaver dem.tif output/ --min-z 8 --max-z 14
        
        # Advanced usage with custom parameters and base URL
        rgb-weaver dem.tif terrain_tiles/ \\
            --min-z 6 --max-z 16 \\
            --workers 8 \\
            --format webp \\
            --base-val -1000 \\
            --interval 0.5 \\
            --name "Alps Terrain" \\
            --attribution "© IGN France" \\
            --base-url "http://localhost:3000/assets/"
    """
    # Configuration du logging
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)
    
    try:
        # Input validation
        logger.info(f"Starting rgb-weaver")
        logger.info(f"Input file: {input_dem}")
        logger.info(f"Output directory: {output_dir}")
        
        # Validate input file
        validate_input_file(input_dem)
        
        # Validate zoom levels
        validate_zoom_levels(min_z, max_z)
        
        # Check output directory
        if output_dir.exists() and not force:
            if not click.confirm(
                f"Directory '{output_dir}' already exists. Continue?",
                default=False
            ):
                logger.info("Operation cancelled by user")
                sys.exit(0)
        
        # Pipeline configuration
        pipeline_config = {
            'min_zoom': min_z,
            'max_zoom': max_z,
            'workers': workers,
            'format': format,
            'base_val': base_val,
            'interval': interval,
            'round_digits': round_digits,
            'scheme': scheme,
            'name': name or input_dem.stem,
            'description': description,
            'attribution': attribution,
            'base_url': base_url,
            'force': force
        }
        
        # Initialize and run pipeline
        pipeline = RGBWeaverPipeline(input_dem, output_dir, **pipeline_config)
        
        logger.info("Starting processing pipeline...")
        pipeline.run()
        
        logger.info("Processing completed successfully!")
        logger.info(f"Results available at: {output_dir}")
        
    except KeyboardInterrupt:
        logger.error("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        if verbose:
            logger.exception("Error details:")
        sys.exit(1)


if __name__ == '__main__':
    main()