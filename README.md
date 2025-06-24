# rgb-weaver

> Enhanced terrain RGB raster tile generator with multiple output formats

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-yellow.svg)](https://github.com/Australes-Inc/rgb-weaver/releases)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://hub.docker.com/r/diegoposba/rgb-weaver)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**rgb-weaver** is a powerful, production-ready tool for generating terrain RGB tiles from Digital Elevation Models (DEMs). It supports multiple output formats and provides a complete workflow from DEM to deployable tiles with just one command.

## Features

- **Multiple Output Formats**:
  - **PMTiles** (.pmtiles) - Modern web-optimized format
  - **MBTiles** (.mbtiles) - SQLite-based format for offline use
  - **PNG/WebP tiles** - Directory structure with optional TileJSON
- **Docker Support**: Ready-to-use container with all dependencies
- **Conda Support**: Ready-to-use `environment.yml` with all dependencies
- **Complete Pipeline**: Automated DEM processing with metadata generation
- **Smart Metadata**: Auto-extracts bounds, center, and elevation statistics
- **Parallel Processing**: Multi-threaded tile generation for optimal performance


## Quick Start

### Local Installation

#### Using Conda

```bash
# Clone the repository
git clone https://github.com/Australes-Inc/rgb-weaver.git
cd rgb-weaver

# Create and activate conda environment
conda env create -f environment.yml
conda activate rgb-weaver

# Install rgb-weaver
pip install -e .
```

#### Using pip

```bash
# Install directly from GitHub
pip install git+https://github.com/Australes-Inc/rgb-weaver.git

# Or install dependencies manually
pip install git+https://github.com/Australes-Inc/mbutil.git
pip install git+https://github.com/Australes-Inc/rio-rgbify.git
pip install click rasterio numpy tqdm
```

### Using Docker

The fastest way to get started is with our pre-built Docker image:

```bash
# Pull the latest image
docker pull your-dockerhub/rgb-weaver:2.0.0

# Generate PMTiles (modern web format)
docker run --rm -v $(pwd):/data your-dockerhub/rgb-weaver:2.0.0 \
  dem.tif terrain.pmtiles --min-z 8 --max-z 14

# Generate MBTiles (offline/mobile apps)
docker run --rm -v $(pwd):/data your-dockerhub/rgb-weaver:2.0.0 \
  dem.tif terrain.mbtiles --min-z 8 --max-z 14

# Generate PNG tiles with metadata
docker run --rm -v $(pwd):/data your-dockerhub/rgb-weaver:2.0.0 \
  dem.tif tiles/ --min-z 8 --max-z 14 --tilejson true
```

## Usage Examples

### Basic Usage

```bash
# PMTiles
rgb-weaver dem.tif terrain.pmtiles --min-z 8 --max-z 14

# MBTiles
rgb-weaver dem.tif terrain.mbtiles --min-z 8 --max-z 14

# PNG/WEBP tiles with TileJSON metadata
rgb-weaver dem.tif tiles/ --min-z 8 --max-z 14 --tilejson true

# PNG/WEBP tiles without metadata (tiles only)
rgb-weaver dem.tif tiles/ --min-z 8 --max-z 14 --tilejson false
```

### Advanced Usage (for Directory + TileJSON)

```bash
# Production deployment with custom metadata
rgb-weaver dem.tif tiles/ \
    --min-z 8 --max-z 14 \
    --base-url "https://tiles.example.com/" \
    --name "Mountain Terrain" \
    --description "High-resolution elevation data" \
    --attribution "© Geological Survey" \
    --tilejson true
```

### Docker Examples

```bash
# Windows (Command Prompt)
docker run --rm -v "%cd%":/data your-dockerhub/rgb-weaver:2.0.0 ^
  dem.tif output.pmtiles --min-z 8 --max-z 14

# Linux/macOS
docker run --rm -v $(pwd):/data your-dockerhub/rgb-weaver:2.0.0 \
  dem.tif output.pmtiles --min-z 8 --max-z 14 --verbose

# With docker-compose
docker-compose run rgb-weaver dem.tif output.pmtiles --min-z 8 --max-z 14
```

## Command Line Options

### Required Arguments

| Option | Description |
|--------|-------------|
| `INPUT_DEM` | Path to input DEM file (GeoTIFF recommended) |
| `OUTPUT` | Output path (.pmtiles, .mbtiles, or directory) |
| `--min-z` | Minimum zoom level (0-22) |
| `--max-z` | Maximum zoom level (0-22) |

### Core Options

| Option | Default | Description |
|--------|---------|-------------|
| `--tilejson` | true | Generate TileJSON metadata (for directory only) |
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
| `--verbose, -v` | Verbose output with detailed logs |
| `--quiet, -q` | Show only errors |
| `--force, -f` | Overwrite existing output |
| `--check-deps` | Check dependencies and platform support |

## Output Formats

- [PMTiles](https://github.com/protomaps/PMTiles)
- [MBTiles](https://github.com/mapbox/mbtiles-spec)
- PNG/WebP Tiles Directory + optional [TileJSON](https://github.com/mapbox/tilejson-spec)

## Supported Input Formats

rgb-weaver supports various raster formats through GDAL:

- **GeoTIFF** (`.tif`, `.tiff`) - *Strongly Recommended*
- **ERDAS Imagine** (`.img`)
- **ENVI formats** (`.bil`, `.bip`, `.bsq`)
- **ASCII Grid** (`.asc`)
- **USGS DEM** (`.dem`)
- **SRTM HGT** (`.hgt`)
- **DTED** (`.dt0`, `.dt1`, `.dt2`)
- **Virtual Raster** (`.vrt`)

## Development

### Project Structure

```
rgb-weaver/
├── rgbweaver/                  # Main package
│   ├── core/                   # Modular architecture
│   │   ├── processors/         # Format-specific processors
│   │   └── outputs/           # Output handlers
│   ├── bin/                   # PMTiles binaries (bundled)
│   ├── cli.py                 # Command line interface
│   ├── metadata.py            # DEM metadata & TileJSON
│   └── utils.py               # Utilities
├── scripts/                   # Docker helper scripts
├── Dockerfile                 # Docker production build
├── docker-compose.yml         # Docker orchestration
└── environment.yml            # Conda environment
```

## Related Projects

- **[rio-rgbify](https://github.com/Australes-Inc/rio-rgbify)**: Enhanced fork for RGB encoding
- **[mbutil](https://github.com/Australes-Inc/mbutil)**: Modernized MBTiles utility
- **[PMTiles](https://github.com/protomaps/PMTiles)**: Modern tile archive format
- **[TileJSON Specification](https://github.com/mapbox/tilejson-spec)**: Metadata standard

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Mapbox** for terrain RGB encoding specification and TileJSON standard
- **Protomaps** for the PMTiles format and [go-pmtiles](https://github.com/protomaps/go-pmtiles) tool
- **Rasterio** team for geospatial Python tools
- **GDAL** community for raster processing capabilities
- Original **rio-rgbify** and **mbutil** developers

## Support

- **Discussions**: [GitHub Discussions](https://github.com/Australes-Inc/rgb-weaver/discussions)
- **Email**: diegoposba@gmail.com

## Author

**Diego Posado Bañuls** ([@diegoposba](https://github.com/diegoposba)) for Australes Inc