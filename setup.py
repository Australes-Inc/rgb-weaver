#!/usr/bin/env python
"""
rgb-weaver: Generate terrain RGB raster tiles directly from a DEM
"""

from setuptools import setup, find_packages
import os

def read_file(filename):
    """Read file contents."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), 'r', encoding='utf-8') as f:
        return f.read()

def get_version():
    """Get version from package."""
    try:
        with open('rgbweaver/__init__.py', 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return '0.1.0'

setup(
    name='rgb-weaver',
    version=get_version(),
    author='Australes Inc',
    author_email='diegoposba@gmail.com',
    description='Generate terrain RGB raster tiles directly from a DEM using gdal, rio-rgbify and mbutil',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/Australes-Inc/rgb-weaver',
    
    packages=find_packages(),
    include_package_data=True,
    
    entry_points={
        'console_scripts': [
            'rgb-weaver=rgbweaver.cli:main',
        ],
    },
    
    install_requires=[
        'click>=8.0',
        'rasterio>=1.3.0',
        'numpy>=1.20.0',
        'tqdm>=4.60.0',
        # 'git+https://github.com/Australes-Inc/mbutil.git',
        # 'git+https://github.com/Australes-Inc/rio-rgbify.git',
    ],
    
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov',
            'black',
            'flake8',
            'pre-commit',
        ],
    },
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
    python_requires='>=3.8',
    license='MIT',
    keywords='tiles terrain rgb raster gdal gis dem elevation',
)