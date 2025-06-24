# setup.py
"""
Setup configuration for rgb-weaver v2.0.0 with modular architecture
"""

from setuptools import setup, find_packages
from pathlib import Path

def get_version():
    """Extract version from package"""
    init_file = Path(__file__).parent / "rgbweaver" / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return "2.0.0"

def get_long_description():
    """Read README file"""
    readme_file = Path(__file__).parent / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="rgb-weaver",
    version=get_version(),
    author="Australes Inc",
    author_email="diegoposba@gmail.com",
    description="Generate terrain RGB raster tiles from DEMs with multiple output formats",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Australes-Inc/rgb-weaver",
    
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'rgbweaver': [
            'bin/pmtiles-*',
        ],
    },
    
    # Entry points for CLI
    entry_points={
        'console_scripts': [
            'rgb-weaver=rgbweaver.cli:cli',
        ],
    },
    
    # Core dependencies
    install_requires=[
        "click>=8.0.0",
        "rasterio>=1.3.0",
        "numpy>=1.20.0",
        "tqdm>=4.60.0",
    ],
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.12.0',
            'black>=21.0.0',
            'flake8>=3.9.0',
            'mypy>=0.910',
        ],
        'test': [
            'pytest>=6.0.0',
            'pytest-cov>=2.12.0',
        ],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    
    python_requires=">=3.8",
    license="MIT",
    keywords="terrain rgb tiles dem mbtiles pmtiles gis raster",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/Australes-Inc/rgb-weaver/issues",
        "Source": "https://github.com/Australes-Inc/rgb-weaver",
        "Documentation": "https://github.com/Australes-Inc/rgb-weaver#readme",
    },
)