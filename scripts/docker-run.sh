# scripts/docker-run.sh
#!/bin/bash
# Convenience script for running rgb-weaver in Docker

set -e

# Default values
WORKERS=4
VERBOSE=""
DATA_DIR=$(pwd)

# Help function
show_help() {
    cat << EOF
rgb-weaver Docker Runner

Usage: $0 [OPTIONS] INPUT OUTPUT --min-z MIN --max-z MAX [RGB_WEAVER_OPTIONS]

Options:
  -w, --workers N     Number of workers (default: 4)
  -v, --verbose       Enable verbose output
  -d, --data-dir DIR  Data directory to mount (default: current directory)
  -h, --help          Show this help

Examples:
  $0 dem.tif terrain.pmtiles --min-z 8 --max-z 14
  $0 -w 8 -v dem.tif tiles/ --min-z 6 --max-z 16 --format webp
  $0 -d /path/to/data input.tif output.mbtiles --min-z 10 --max-z 15

Docker equivalent:
  docker run -v \$(pwd):/data rgb-weaver:latest dem.tif output.pmtiles --min-z 8 --max-z 14
EOF
}

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # Remaining arguments go to rgb-weaver
            break
            ;;
    esac
done

# Check if we have arguments for rgb-weaver
if [[ $# -eq 0 ]]; then
    echo "Error: No arguments provided for rgb-weaver"
    echo ""
    show_help
    exit 1
fi

echo "Running rgb-weaver in Docker..."
echo "Data directory: $DATA_DIR"
echo "Workers: $WORKERS"
echo "Command: rgb-weaver $VERBOSE --workers $WORKERS $*"
echo ""

# Run Docker with mounted volume
docker run --rm \
    -v "$DATA_DIR:/data" \
    rgb-weaver:latest \
    $VERBOSE --workers $WORKERS "$@"

echo ""
echo "rgb-weaver completed!"