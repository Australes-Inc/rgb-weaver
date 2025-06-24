# scripts/docker-test.sh
#!/bin/bash
# Test script for rgb-weaver Docker image

set -e

echo "Testing rgb-weaver Docker image..."

# Test 1: Version check
echo "Testing --version..."
docker run --rm rgb-weaver:latest --version

# Test 2: Dependencies check
echo ""
echo "Testing --check-deps..."
docker run --rm rgb-weaver:latest --check-deps

# Test 3: Help command
echo ""
echo "Testing --help..."
docker run --rm rgb-weaver:latest --help | head -10

# Test 4: Create test DEM and process (if Python available)
if command -v python3 &> /dev/null; then
    echo ""
    echo "Creating test DEM and processing..."
    
    # Create test DEM
    python3 -c "
import numpy as np
import rasterio
from rasterio.transform import from_bounds

# Create a simple test DEM
data = np.random.randint(0, 1000, (50, 50), dtype=np.uint16)
transform = from_bounds(-1, -1, 1, 1, 50, 50)

with rasterio.open('test_dem.tif', 'w', 
                   driver='GTiff', height=50, width=50, count=1, 
                   dtype=data.dtype, crs='EPSG:4326', transform=transform) as dst:
    dst.write(data, 1)

print('Test DEM created: test_dem.tif')
"
    
    # Test with the DEM
    echo "   Processing test DEM..."
    docker run --rm -v $(pwd):/data rgb-weaver:latest \
        test_dem.tif test_output.pmtiles --min-z 8 --max-z 10 --verbose
    
    # Check output
    if [ -f "test_output.pmtiles" ]; then
        echo "   PMTiles output created successfully!"
        ls -lh test_output.pmtiles
        rm -f test_dem.tif test_output.pmtiles
    else
        echo "   PMTiles output not found"
        exit 1
    fi
else
    echo ""
    echo "Skipping DEM test (Python not available)"
fi

echo ""
echo "All Docker tests passed!"
echo ""
echo "Ready to use:"
echo "  docker run -v \$(pwd):/data rgb-weaver:latest dem.tif output.pmtiles --min-z 8 --max-z 14"