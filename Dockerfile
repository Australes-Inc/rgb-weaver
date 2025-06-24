# Dockerfile.conda - rgb-weaver with conda for better geospatial support
# Alternative approach using conda-forge for consistent geospatial stack

FROM continuumio/miniconda3:latest

# Metadata
LABEL maintainer="Australes Inc <diegoposba@gmail.com>"
LABEL description="rgb-weaver: Enhanced terrain RGB tile generator (conda version)"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONDA_ALWAYS_YES=true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create conda environment with geospatial stack
RUN conda create -n rgbweaver python=3.11 && \
    conda clean -a

# Activate environment and install geospatial packages from conda-forge
SHELL ["conda", "run", "-n", "rgbweaver", "/bin/bash", "-c"]

# Install geospatial stack from conda-forge (ensures compatibility)
RUN conda install -c conda-forge \
    rasterio=1.3.* \
    gdal \
    proj \
    geos \
    numpy \
    click \
    tqdm \
    pillow \
    git \
    pip \
    && conda clean -a

# Install additional dependencies via pip
RUN pip install --no-cache-dir \
    git+https://github.com/Australes-Inc/mbutil.git \
    git+https://github.com/Australes-Inc/rio-rgbify.git

# Create non-root user
RUN groupadd -r rgbweaver && \
    useradd -r -g rgbweaver -d /app -s /bin/bash rgbweaver

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install rgb-weaver
RUN pip install --no-cache-dir -e .

# Ensure PMTiles binaries are executable
RUN chmod +x /app/rgbweaver/bin/pmtiles-*

# Create data directory
RUN mkdir -p /data && \
    chown -R rgbweaver:rgbweaver /app /data

# Test installation
RUN python -c "import rasterio; from rasterio.crs import CRS; print('PROJ test passed:', CRS.from_epsg(4326))"
RUN rgb-weaver --version

# Switch to non-root user
USER rgbweaver

# Set default working directory for data
WORKDIR /data

# Create conda activation script
RUN echo '#!/bin/bash\nconda run -n rgbweaver rgb-weaver "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD conda run -n rgbweaver rgb-weaver --version || exit 1

# Use conda activation script as entrypoint
ENTRYPOINT ["conda", "run", "-n", "rgbweaver", "rgb-weaver"]
CMD ["--help"]