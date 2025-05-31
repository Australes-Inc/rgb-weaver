"""
DEM metadata extraction and TileJSON generation for rgb-weaver
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

import rasterio
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

from rgbweaver.config import (
    DEFAULT_TILEJSON_VERSION, DEFAULT_VERSION, DEFAULT_ATTRIBUTION,
    DEFAULT_ENCODING, DEFAULT_TILE_SIZE
)
from rgbweaver.utils import RGBWeaverError

logger = logging.getLogger(__name__)


class MetadataError(RGBWeaverError):
    """Error during metadata extraction or TileJSON generation."""
    pass


@dataclass
class DEMInfo:
    """Container for DEM metadata information."""
    width: int
    height: int
    bands: int
    crs: Optional[CRS]
    bounds: Tuple[float, float, float, float]  # (left, bottom, right, top)
    bounds_wgs84: Tuple[float, float, float, float]  # WGS84 bounds
    center_wgs84: Tuple[float, float]  # (lon, lat)
    min_value: Optional[float]
    max_value: Optional[float]
    nodata: Optional[float]
    dtype: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'width': self.width,
            'height': self.height,
            'bands': self.bands,
            'crs': str(self.crs) if self.crs else None,
            'bounds': self.bounds,
            'bounds_wgs84': self.bounds_wgs84,
            'center_wgs84': self.center_wgs84,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'nodata': self.nodata,
            'dtype': self.dtype
        }


class DEMMetadata:
    """Extract metadata from DEM files using GDAL/rasterio."""
    
    def __init__(self, dem_path: Union[str, Path]):
        """
        Initialize metadata extractor.
        
        Args:
            dem_path: Path to DEM file
        """
        self.dem_path = Path(dem_path)
        self._info: Optional[DEMInfo] = None
        
    def extract(self, compute_stats: bool = True) -> DEMInfo:
        """
        Extract all metadata from DEM.
        
        Args:
            compute_stats: Whether to compute min/max statistics
            
        Returns:
            DEMInfo: Extracted metadata
            
        Raises:
            MetadataError: If extraction fails
        """
        logger.info(f"Extracting metadata from: {self.dem_path}")
        
        try:
            with rasterio.open(self.dem_path) as src:
                # Basic raster info
                width = src.width
                height = src.height
                bands = src.count
                crs = src.crs
                bounds = src.bounds
                nodata = src.nodata
                dtype = str(src.dtype)
                
                logger.debug(f"Raster info: {width}x{height}, {bands} bands, CRS: {crs}")
                
                # Transform bounds to WGS84 for TileJSON
                bounds_wgs84 = self._transform_bounds_to_wgs84(bounds, crs)
                center_wgs84 = self._calculate_center(bounds_wgs84)
                
                # Compute statistics if requested
                min_value = None
                max_value = None
                if compute_stats:
                    min_value, max_value = self._compute_statistics(src)
                
                self._info = DEMInfo(
                    width=width,
                    height=height,
                    bands=bands,
                    crs=crs,
                    bounds=bounds,
                    bounds_wgs84=bounds_wgs84,
                    center_wgs84=center_wgs84,
                    min_value=min_value,
                    max_value=max_value,
                    nodata=nodata,
                    dtype=dtype
                )
                
                logger.info(f" Metadata extracted successfully")
                logger.debug(f"Bounds (WGS84): {bounds_wgs84}")
                logger.debug(f"Center (WGS84): {center_wgs84}")
                if compute_stats:
                    logger.debug(f"Value range: {min_value} to {max_value}")
                
                return self._info
                
        except Exception as e:
            raise MetadataError(f"Failed to extract metadata: {e}")
    
    def _transform_bounds_to_wgs84(
        self, 
        bounds: Tuple[float, float, float, float], 
        src_crs: Optional[CRS]
    ) -> Tuple[float, float, float, float]:
        """
        Transform bounds to WGS84 coordinates.
        
        Args:
            bounds: Source bounds (left, bottom, right, top)
            src_crs: Source CRS
            
        Returns:
            WGS84 bounds (left, bottom, right, top)
        """
        if src_crs is None:
            logger.warning("No CRS defined, assuming bounds are already in WGS84")
            return bounds
        
        if src_crs == CRS.from_epsg(4326):
            # Already WGS84
            return bounds
        
        try:
            # Transform bounds to WGS84
            wgs84_bounds = transform_bounds(
                src_crs, 
                CRS.from_epsg(4326), 
                *bounds
            )
            
            # Ensure bounds are within valid WGS84 range
            left, bottom, right, top = wgs84_bounds
            left = max(-180.0, min(180.0, left))
            right = max(-180.0, min(180.0, right))
            bottom = max(-90.0, min(90.0, bottom))
            top = max(-90.0, min(90.0, top))
            
            return (left, bottom, right, top)
            
        except Exception as e:
            logger.warning(f"Failed to transform bounds to WGS84: {e}")
            # Fallback to original bounds
            return bounds
    
    def _calculate_center(
        self, 
        bounds: Tuple[float, float, float, float]
    ) -> Tuple[float, float]:
        """
        Calculate center point from bounds.
        
        Args:
            bounds: Bounds (left, bottom, right, top)
            
        Returns:
            Center coordinates (lon, lat)
        """
        left, bottom, right, top = bounds
        center_lon = (left + right) / 2
        center_lat = (bottom + top) / 2
        return (center_lon, center_lat)
    
    def _compute_statistics(self, src: rasterio.DatasetReader) -> Tuple[Optional[float], Optional[float]]:
        """
        Compute min/max statistics from the first band.
        
        Args:
            src: Rasterio dataset
            
        Returns:
            (min_value, max_value) tuple
        """
        logger.debug("Computing raster statistics...")
        
        try:
            # Read statistics from first band
            band = src.read(1, masked=True)
            
            if band.mask.all():
                logger.warning("All pixels are masked/nodata")
                return None, None
            
            min_val = float(band.min())
            max_val = float(band.max())
            
            logger.debug(f"Statistics computed: min={min_val}, max={max_val}")
            return min_val, max_val
            
        except Exception as e:
            logger.warning(f"Failed to compute statistics: {e}")
            return None, None
    
    @property
    def info(self) -> Optional[DEMInfo]:
        """Get extracted metadata info."""
        return self._info


class TileJSONGenerator:
    """Generate TileJSON files according to Mapbox specification with extensions."""
    
    def __init__(self, dem_info: DEMInfo):
        """
        Initialize TileJSON generator.
        
        Args:
            dem_info: DEM metadata information
        """
        self.dem_info = dem_info
    
    def generate(
        self,
        name: str,
        min_zoom: int,
        max_zoom: int,
        format: str = "png",
        scheme: str = "xyz",
        description: Optional[str] = None,
        attribution: str = DEFAULT_ATTRIBUTION,
        tile_url_template: str = "./{z}/{x}/{y}.{format}",
        **kwargs
    ) -> Dict:
        """
        Generate TileJSON dictionary.
        
        Args:
            name: Tileset name
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
            format: Tile format (png, webp)
            scheme: Tile scheme (xyz, tms, etc.)
            description: Tileset description
            attribution: Attribution string
            tile_url_template: URL template for tiles
            **kwargs: Additional custom fields
            
        Returns:
            TileJSON dictionary
        """
        logger.info(f"Generating TileJSON for '{name}'")
        
        # Basic TileJSON structure
        tilejson = {
            "tilejson": DEFAULT_TILEJSON_VERSION,
            "name": name,
            "version": DEFAULT_VERSION,
            "scheme": scheme,
            "tiles": [tile_url_template.format(format=format)],
            "minzoom": min_zoom,
            "maxzoom": max_zoom,
            "bounds": list(self.dem_info.bounds_wgs84),
            "center": list(self.dem_info.center_wgs84) + [min_zoom],
            "format": format,
            "attribution": attribution
        }
        
        # Add description if provided
        if description:
            tilejson["description"] = description
        else:
            tilejson["description"] = f"Terrain RGB tiles generated from DEM"
        
        # Add Mapbox extensions for terrain RGB
        tilejson["encoding"] = DEFAULT_ENCODING
        tilejson["tileSize"] = DEFAULT_TILE_SIZE
        
        # Add custom fields
        for key, value in kwargs.items():
            if key not in tilejson:  # Don't override standard fields
                tilejson[key] = value
        
        logger.info(" TileJSON generated successfully")
        return tilejson
    
    def save(
        self,
        output_path: Union[str, Path],
        name: str,
        min_zoom: int,
        max_zoom: int,
        **kwargs
    ) -> Path:
        """
        Generate and save TileJSON file.
        
        Args:
            output_path: Output file path
            name: Tileset name
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
            **kwargs: Additional arguments for generate()
            
        Returns:
            Path to saved file
            
        Raises:
            MetadataError: If saving fails
        """
        output_path = Path(output_path)
        
        try:
            # Generate TileJSON
            tilejson_data = self.generate(
                name=name,
                min_zoom=min_zoom,
                max_zoom=max_zoom,
                **kwargs
            )
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tilejson_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"TileJSON saved to: {output_path}")
            return output_path
            
        except Exception as e:
            raise MetadataError(f"Failed to save TileJSON: {e}")


def extract_dem_metadata(dem_path: Union[str, Path], compute_stats: bool = True) -> DEMInfo:
    """
    Convenience function to extract DEM metadata.
    
    Args:
        dem_path: Path to DEM file
        compute_stats: Whether to compute min/max statistics
        
    Returns:
        DEMInfo: Extracted metadata
    """
    extractor = DEMMetadata(dem_path)
    return extractor.extract(compute_stats=compute_stats)


def generate_tilejson(
    dem_info: DEMInfo,
    output_path: Union[str, Path],
    name: str,
    min_zoom: int,
    max_zoom: int,
    **kwargs
) -> Path:
    """
    Convenience function to generate and save TileJSON.
    
    Args:
        dem_info: DEM metadata information
        output_path: Output file path
        name: Tileset name
        min_zoom: Minimum zoom level
        max_zoom: Maximum zoom level
        **kwargs: Additional arguments
        
    Returns:
        Path to saved file
    """
    generator = TileJSONGenerator(dem_info)
    return generator.save(output_path, name, min_zoom, max_zoom, **kwargs)