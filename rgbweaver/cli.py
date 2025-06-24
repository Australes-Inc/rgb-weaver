# rgbweaver/cli.py (VERSION FINALE avec gestion d'erreurs robuste)
"""
Final CLI for rgb-weaver Phase 2 with comprehensive error handling
"""

import click
import sys
import traceback
from pathlib import Path

from .core import Pipeline, OutputFactory, OutputType
from .utils import check_dependencies, validate_zoom_levels, ensure_output_dir, format_file_size


def show_platform_support():
    """Show supported output formats on current platform"""
    supported_types = OutputFactory.get_supported_types()
    
    click.echo("Platform Support:")
    for output_type in [OutputType.MBTILES, OutputType.PMTILES, OutputType.TILES_WITH_JSON, OutputType.TILES]:
        status = "Ok" if output_type in supported_types else "Error"
        click.echo(f"  {status} {output_type.value}: {output_type.description}")


@click.command()
@click.argument('input_dem', type=click.Path(exists=True, path_type=Path), required=False)
@click.argument('output', type=click.Path(path_type=Path), required=False)
@click.option('--min-z', type=int, help='Minimum zoom level (0-22)')
@click.option('--max-z', type=int, help='Maximum zoom level (0-22)')
@click.option('--tilejson', type=bool, default=True, 
              help='Generate TileJSON metadata for tiles output (default: true)')
@click.option('--workers', '-j', type=int, default=4, 
              help='Number of parallel workers (default: 4)')
@click.option('--format', 'format_type', type=click.Choice(['png', 'webp']), default='png',
              help='Output tile format (default: png)')
@click.option('--base-val', '-b', type=float, default=-10000,
              help='Base value for RGB encoding (default: -10000)')
@click.option('--interval', '-i', type=float, default=0.1,
              help='Precision interval for encoding (default: 0.1)')
@click.option('--round-digits', '-r', type=int, default=0,
              help='Number of digits to round (default: 0)')
@click.option('--scheme', type=click.Choice(['xyz', 'tms', 'zyx', 'wms']), default='xyz',
              help='Tile naming scheme (default: xyz)')
@click.option('--name', type=str, help='Tileset name (default: DEM filename)')
@click.option('--description', type=str, default='', help='Tileset description')
@click.option('--attribution', type=str, default='', help='Attribution string')
@click.option('--base-url', type=str, default='', 
              help='Base URL for tile server (for TileJSON)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed logs')
@click.option('--quiet', '-q', is_flag=True, help='Show only errors and warnings')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output')
@click.option('--check-deps', is_flag=True, help='Check dependencies and platform support')
@click.option('--version', is_flag=True, help='Show version information')
def main(input_dem: Path,
         output: Path,
         min_z: int,
         max_z: int,
         tilejson: bool,
         workers: int,
         format_type: str,
         base_val: float,
         interval: float,
         round_digits: int,
         scheme: str,
         name: str,
         description: str,
         attribution: str,
         base_url: str,
         verbose: bool,
         quiet: bool,
         force: bool,
         check_deps: bool,
         version: bool):
    """
    Generate terrain RGB raster tiles from DEMs with multiple output formats
    
    INPUT_DEM: Path to input DEM file (GeoTIFF, SRTM, etc.)
    OUTPUT: Output path (.mbtiles, .pmtiles, or directory for tiles)
    
    Examples:
    
    \b
    PMTiles for modern web mapping:
    rgb-weaver dem.tif terrain.pmtiles --min-z 8 --max-z 14
    
    \b
    MBTiles for offline applications:
    rgb-weaver dem.tif terrain.mbtiles --min-z 8 --max-z 14
    
    \b
    PNG tiles with TileJSON for custom servers:
    rgb-weaver dem.tif tiles/ --min-z 8 --max-z 14 --base-url "https://tiles.example.com/"
    
    \b
    High-performance WebP tiles:
    rgb-weaver dem.tif tiles/ --min-z 10 --max-z 16 --format webp --workers 8
    """
    
    # Handle version flag
    if version:
        from . import __version__
        click.echo(f"rgb-weaver version {__version__}")
        click.echo("Enhanced terrain RGB tile generator with multiple output formats")
        sys.exit(0)
    
    # Handle dependency/platform check
    if check_deps:
        try:
            click.echo("Checking dependencies and platform support...\n")
            deps = check_dependencies(required_only=False)
            click.echo("Dependency check completed:")
            for dep, available in deps.items():
                status = "Available" if available else "Missing"
                click.echo(f"  {dep}: {status}")
            
            click.echo()
            show_platform_support()
            sys.exit(0)
        except Exception as e:
            click.echo(f"Dependency check failed: {e}", err=True)
            sys.exit(1)
    
    # Validate required arguments
    if not input_dem or not output:
        click.echo("Error: INPUT_DEM and OUTPUT are required arguments", err=True)
        click.echo("Use --help for usage information")
        sys.exit(1)
    
    if min_z is None or max_z is None:
        click.echo("Error: --min-z and --max-z are required", err=True)
        click.echo("Example: rgb-weaver dem.tif output.pmtiles --min-z 8 --max-z 14")
        sys.exit(1)
    
    # Handle conflicting verbosity options
    if verbose and quiet:
        click.echo("Error: --verbose and --quiet cannot be used together", err=True)
        sys.exit(1)
    
    try:
        # Validate output format support
        try:
            output_type = OutputFactory.detect_output_type(str(output), tilejson)
            supported_types = OutputFactory.get_supported_types()
            
            if output_type not in supported_types:
                click.echo(f"Error: {output_type.value} format not supported on this platform", err=True)
                click.echo("\nSupported formats on this platform:")
                for supported_type in supported_types:
                    click.echo(f"  {supported_type.value}: {supported_type.description}")
                sys.exit(1)
                
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        
        # Check core dependencies
        if not quiet:
            click.echo("Checking dependencies...")
        check_dependencies(required_only=True)
        
        # Validate inputs
        validate_zoom_levels(min_z, max_z)
        
        # Ensure output path is valid
        ensure_output_dir(output, force)
        
        # Set default name if not provided
        if not name:
            name = input_dem.stem
        
        # Show processing info
        if not quiet:
            click.echo(f"\nStarting rgb-weaver pipeline")
            click.echo(f"Input: {input_dem}")
            click.echo(f"Output: {output} ({output_type.value})")
            click.echo(f"Zoom range: {min_z}-{max_z} ({max_z - min_z + 1} levels)")
        
        # Create pipeline
        pipeline = Pipeline(verbose=verbose, quiet=quiet)
        
        # Prepare processing arguments
        process_kwargs = {
            'workers': workers,
            'format': format_type,
            'base_val': base_val,
            'interval': interval,
            'round_digits': round_digits,
            'scheme': scheme,
            'name': name,
            'description': description or f'Terrain RGB tiles generated from {input_dem.name}',
            'attribution': attribution,
            'base_url': base_url
        }
        
        # Execute pipeline
        result = pipeline.process(
            dem_path=str(input_dem),
            output_path=str(output),
            min_z=min_z,
            max_z=max_z,
            tilejson=tilejson,
            **process_kwargs
        )
        
        if not quiet:
            click.echo(f"\nSuccess! Generated {result['output_type']}: {result['output_path']}")
            
            # Show enhanced summary
            metadata = result.get('metadata', {})
            if metadata.get('total_tiles'):
                click.echo(f"Total tiles: {metadata['total_tiles']:,}")
            
            # Show file size information
            if metadata.get('file_size_bytes'):
                size_str = format_file_size(metadata['file_size_bytes'])
                click.echo(f"File size: {size_str}")
            elif metadata.get('total_size_bytes'):
                size_str = format_file_size(metadata['total_size_bytes'])
                click.echo(f"Total size: {size_str}")
            
            # Show compression info for PMTiles
            if metadata.get('compression_ratio_percent'):
                ratio = metadata['compression_ratio_percent']
                click.echo(f"PMTiles compression: {ratio}% size reduction")
            
            # Show processing time
            if result.get('total_time_seconds'):
                time_str = f"{result['total_time_seconds']:.1f}s"
                click.echo(f"Total time: {time_str}")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        if not quiet:
            click.echo("\nOperation cancelled by user", err=True)
        sys.exit(130)
        
    except Exception as e:
        if verbose:
            click.echo(f"\nError occurred:", err=True)
            traceback.print_exc()
        else:
            click.echo(f"Error: {e}", err=True)
            if not quiet:
                click.echo("Use --verbose for detailed error information")
        sys.exit(1)


def cli():
    """Entry point for console script"""
    main()


if __name__ == '__main__':
    cli()