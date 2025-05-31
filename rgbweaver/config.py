"""
Default configuration for rgb-weaver
"""

# Default parameters for rio-rgbify
DEFAULT_BASE_VAL = -10000
DEFAULT_INTERVAL = 0.1
DEFAULT_ROUND_DIGITS = 0
DEFAULT_WORKERS = 4
DEFAULT_FORMAT = "png"

# Default parameters for mbutil
DEFAULT_SCHEME = "xyz"

# Default parameters for TileJSON
DEFAULT_TILEJSON_VERSION = "3.0.0"
DEFAULT_VERSION = "1.0.0"
DEFAULT_ATTRIBUTION = "Generated with rgb-weaver"
DEFAULT_ENCODING = "mapbox"
DEFAULT_TILE_SIZE = 512

# Supported raster formats
SUPPORTED_RASTER_FORMATS = [
    '.tif', '.tiff',    # GeoTIFF (primary)
    '.img',             # ERDAS Imagine
    '.bil', '.bip', '.bsq',  # ENVI formats
    '.asc',             # ASCII Grid
    '.dem',             # USGS DEM
    '.hgt',             # SRTM HGT
    '.dt0', '.dt1', '.dt2',  # DTED
    '.vrt',             # Virtual Raster
]

# File size limit (in MB) 
MAX_FILE_SIZE_MB = 10240 

# Zoom level limits
MIN_ZOOM_LEVEL = 0
MAX_ZOOM_LEVEL = 22

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'