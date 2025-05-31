# rgb-weaver

> Generate terrain RGB raster tiles directly from a DEM using GDAL, rio-rgbify and mbutil

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Packages](https://img.shields.io/badge/forked_package-rio_rgbify-blue.svg)](https://github.com/Australes-Inc/rio-rgbify)
[![Packages](https://img.shields.io/badge/forked_package-mbutil-blue.svg)](https://github.com/Australes-Inc/mbutil)
[![Packages](https://img.shields.io/badge/package-gdal-brightgreen.svg)](https://github.com/Australes-Inc/mbutil)

**rgb-weaver** automates the complete workflow for generating terrain RGB tiles from Digital Elevation Models (DEMs). It orchestrates multiple tools to create production-ready tilesets with proper metadata in a single command.

## Features

- **Complete Pipeline**: DEM → MBTiles → Individual Tiles → TileJSON metadata
- **Automatic Projection**: Handles coordinate system transformations to WGS84
- **Smart Metadata**: Auto-extracts bounds, center, and elevation statistics
- **TileJSON Ready**: Generates Mapbox/Maplibre-compatible tiles.json with proper encoding
- **Parallel Processing**: Multi-threaded tile generation for optimal performance
- **Flexible Configuration**: Extensive customization options for all parameters
- **Server Ready**: Optional base URL configuration for direct deployment

## Quick Start

### Installation

#### Using Conda

```bash
# Clone the repository
git clone https://github.com/Australes-Inc/rgb-weaver.git
cd rgb-weaver

# Create and activate conda environment
conda env create -f environment.yml
conda activate rgb-weaver

# Install rgb-weaver in development mode
pip install -e .
```

#### Manual Installation

```bash
# Install dependencies
pip install git+https://github.com/Australes-Inc/mbutil.git
pip install git+https://github.com/Australes-Inc/rio-rgbify.git
pip install click rasterio numpy tqdm

# Install rgb-weaver
pip install git+https://github.com/Australes-Inc/rgb-weaver.git
```

### Basic Usage

```bash
# Simple terrain RGB tile generation
rgb-weaver dem.tif output/ --min-z 8 --max-z 14

# With custom parameters
rgb-weaver dem.tif terrain_tiles/ \
    --min-z 6 --max-z 16 \
    --workers 8 \
    --format webp \
    --base-val -1000 \
    --interval 0.5 \
    --name "My Terrain" \
    --attribution "© My Organization"

# With server URL for direct deployment
rgb-weaver dem.tif public_tiles/ \
    --min-z 8 --max-z 14 \
    --base-url "https://tiles.example.com/assets/" \
    --name "Production Terrain"
```

## Output Structure

```
output/
├── tiles.json          # TileJSON metadata (Mapbox/Maplibre compatible)
└── tiles/              # Terrain RGB tiles
    ├── 8/              # Zoom level 8
    │   ├── 123/
    │   │   ├── 456.png
    │   │   └── 457.png
    │   └── 124/
    ├── 9/              # Zoom level 9
    └── ...
```

## Command Line Options

### Required Arguments

| Option |  Description |
|--------| -------------|
| `INPUT_DEM` | Path to input DEM file (GeoTIFF recommended) |
| `OUTPUT_DIR` | Output directory for tiles and metadata |
| `--min-z` | Minimum zoom level (0-22) |
| `--max-z` | Maximum zoom level (0-22) |

### Core Options

| Option | Default | Description |
|--------|---------|-------------|
| `--workers, -j` | 4 | Number of parallel workers |
| `--format` | png | Output tile format (png, webp) |
| `--base-val, -b` | -10000 | Base value for RGB encoding |
| `--interval, -i` | 0.1 | Precision interval for encoding |
| `--round-digits, -r` | 0 | Number of digits to round |
| `--scheme` | xyz | Tile naming scheme (xyz, tms, zyx, wms) |

### Metadata Options

| Option | Description |
|--------|-------------|
| `--name` | Tileset name (default: DEM filename) |
| `--description` | Tileset description |
| `--attribution` | Attribution string |
| `--base-url` | Base URL for tile server |

### Control Options

| Option | Description |
|--------|-------------|
| `--verbose, -v` | Verbose output for debugging |
| `--quiet, -q` | Show only errors |
| `--force, -f` | Overwrite existing output directory |

## Supported Input Formats

rgb-weaver supports various raster formats through GDAL:

- **GeoTIFF** (`.tif`, `.tiff`) - *Recommended*
- **ERDAS Imagine** (`.img`)
- **ENVI formats** (`.bil`, `.bip`, `.bsq`)
- **ASCII Grid** (`.asc`)
- **USGS DEM** (`.dem`)
- **SRTM HGT** (`.hgt`)
- **DTED** (`.dt0`, `.dt1`, `.dt2`)
- **Virtual Raster** (`.vrt`)

## TileJSON Output

rgb-weaver generates TileJSON 3.0.0 compatible metadata with Mapbox/Maplibre terrain extensions:

```json
{
  "tilejson": "3.0.0",
  "name": "My Terrain",
  "version": "1.0.0",
  "scheme": "xyz",
  "tiles": [
    "https://tiles.example.com/assets/terrain_tiles/tiles/{z}/{x}/{y}.png"
  ],
  "minzoom": 8,
  "maxzoom": 14,
  "bounds": [-140.25, -8.97, -140.01, -8.78],
  "center": [-140.13, -8.87, 8],
  "format": "png",
  "attribution": "© My Organization",
  "description": "Terrain RGB tiles generated from DEM",
  "encoding": "mapbox",
  "tileSize": 512
}
```

### Key Features

- **Automatic bounds**: Extracted and transformed to WGS84
- **Smart center**: Calculated from bounds with appropriate zoom
- **Mapbox encoding**: Compatible with Mapbox/Maplibre GL terrain layers
- **Flexible URLs**: Support for both relative and absolute tile URLs

## Advanced Usage

### Custom RGB Encoding

```bash
# High precision for detailed terrain
rgb-weaver dem.tif output/ \
    --min-z 10 --max-z 16 \
    --base-val 0 \
    --interval 0.01 \
    --round-digits 2

# Optimized for web delivery
rgb-weaver dem.tif output/ \
    --min-z 6 --max-z 14 \
    --format webp \
    --workers 12
```

### Server Deployment

```bash
# Generate tiles for specific server structure
rgb-weaver dem.tif mountain_terrain/ \
    --min-z 8 --max-z 15 \
    --base-url "https://cdn.example.com/terrain/" \
    --name "Mountain Terrain" \
    --attribution "© Geological Survey"
```

### Batch Processing

```bash
# Process multiple DEMs
for dem in *.tif; do
    name=$(basename "$dem" .tif)
    rgb-weaver "$dem" "output_${name}/" \
        --min-z 8 --max-z 12 \
        --name "$name" \
        --verbose
done
```

## Development

### Project Structure

```
rgb-weaver/
├── rgbweaver/
│   ├── __init__.py
│   ├── cli.py              # Command line interface
│   ├── pipeline.py         # Main processing pipeline
│   ├── metadata.py         # DEM metadata & TileJSON generation
│   ├── utils.py            # Utility functions
│   └── config.py           # Default configuration
├── environment.yml         # Conda environment
├── setup.py               # Package setup
├── pyproject.toml         # Modern Python packaging
└── README.md
```

## Related Projects

- **[rio-rgbify](https://github.com/Australes-Inc/rio-rgbify)**: Enhanced fork for RGB encoding
- **[mbutil](https://github.com/Australes-Inc/mbutil)**: Modernized MBTiles utility
- **[TileJSON Specification](https://github.com/mapbox/tilejson-spec)**: Metadata standard

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Mapbox** for the terrain RGB encoding specification and TileJSON standard
- **Rasterio** team for excellent geospatial Python tools
- **GDAL** community for comprehensive raster processing capabilities
- Original **rio-rgbify** and **mbutil** developers

## Support

- **Discussions**: [GitHub Discussions](https://github.com/Australes-Inc/rgb-weaver/discussions)
- **Email**: diegoposba@gmail.com

## Author

**Diego Posado Bañuls** ([@diegoposba](https://github.com/diegoposba)) for Australes Inc

