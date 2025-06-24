# scripts/docker-build.sh
#!/bin/bash
# Build script for rgb-weaver Docker image

set -e

echo "Building rgb-weaver Docker image..."

# Build with build args for optimization
docker build \
    --tag rgb-weaver:latest \
    --tag rgb-weaver:2.0.0 \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

echo "Docker image built successfully!"
echo ""
echo "Quick test:"
docker run --rm rgb-weaver:latest --version

echo ""
echo "Available commands:"
echo "  docker run -v \$(pwd):/data rgb-weaver:latest --help"
echo "  docker run -v \$(pwd):/data rgb-weaver:latest --check-deps"
echo "  docker run -v \$(pwd):/data rgb-weaver:latest dem.tif output.pmtiles --min-z 8 --max-z 14"
