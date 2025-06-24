"""
Enhanced utility functions for rgb-weaver with PMTiles binary support
"""

import subprocess
import sys
import shutil
import platform
from pathlib import Path
from typing import Optional, List, Dict


class RGBWeaverError(Exception):
    """Base exception for rgb-weaver errors."""
    pass


def run_command(cmd: List[str], 
                cwd: Optional[str] = None,
                capture_output: bool = True,
                check: bool = True,
                verbose: bool = False) -> subprocess.CompletedProcess:
    """
    Run a command with proper error handling and verbose output
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        verbose: Whether to print command and output
        
    Returns:
        CompletedProcess result
    """
    if verbose:
        print(f" Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        
        if verbose and result.stdout:
            print(f" Output: {result.stdout.strip()}")
        
        return result
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(cmd)}"
        if e.stderr:
            error_msg += f"\n Error: {e.stderr.strip()}"
        if e.stdout and verbose:
            error_msg += f"\n Output: {e.stdout.strip()}"
        raise RuntimeError(error_msg) from e
        
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Command not found: '{cmd[0]}'. "
            f"Please ensure it's installed and in PATH."
        ) from e


def check_dependencies(required_only: bool = False) -> Dict[str, bool]:
    """
    Enhanced dependency check with bundled PMTiles support
    
    Args:
        required_only: If True, only check core dependencies
        
    Returns:
        Dict mapping dependency names to availability status
        
    Raises:
        RuntimeError: If required dependencies are missing
    """
    # Core dependencies always required
    core_deps = {
        'rio': {
            'command': 'rio',
            'check_args': ['--help'],
            'install_cmd': 'pip install rasterio[s3]',
            'description': 'Rasterio CLI (for rio-rgbify)'
        }
    }
    
    # Optional dependencies for specific formats
    optional_deps = {
        'mb-util': {
            'command': 'mb-util',
            'check_args': ['--help'],
            'install_cmd': 'pip install git+https://github.com/Australes-Inc/mbutil.git',
            'description': 'MBUtil (for PNG tiles extraction)'
        }
    }
    
    # Special handling for PMTiles (bundled binary)
    pmtiles_status = check_bundled_pmtiles()
    optional_deps['pmtiles'] = {
        'available': pmtiles_status['available'],
        'description': f'PMTiles (bundled binary) - {pmtiles_status["message"]}'
    }
    
    dependencies = core_deps.copy()
    if not required_only:
        dependencies.update(optional_deps)
    
    results = {}
    missing_core = []
    missing_optional = []
    
    for name, config in dependencies.items():
        if name == 'pmtiles':
            # Special handling for bundled PMTiles
            results[name] = config['available']
            if not config['available']:
                missing_optional.append(f"  {name}: {config['description']}")
        else:
            try:
                result = subprocess.run(
                    [config['command']] + config['check_args'],
                    capture_output=True,
                    check=True,
                    timeout=10
                )
                results[name] = True
                
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                results[name] = False
                
                if name in core_deps:
                    missing_core.append(f"  {name}: {config['description']}")
                    missing_core.append(f"      Install: {config['install_cmd']}")
                else:
                    missing_optional.append(f"  {name}: {config['description']}")
                    missing_optional.append(f"      Install: {config['install_cmd']}")
    
    # Report missing dependencies
    if missing_core:
        error_msg = " Missing required dependencies:\n" + "\n".join(missing_core)
        if missing_optional:
            error_msg += "\n\nMissing optional dependencies:\n" + "\n".join(missing_optional)
        raise RuntimeError(error_msg)
    
    if missing_optional:
        print("Optional dependencies status:")
        print("\n".join(missing_optional))
    
    return results


def check_bundled_pmtiles() -> Dict[str, any]:
    """
    Check if bundled PMTiles binary is available for current platform
    
    Returns:
        Dict with availability status and message
    """
    try:
        from rgbweaver.core.processors.pmtiles import PMTilesProcessor
        
        # Try to initialize processor (this will check for binary)
        processor = PMTilesProcessor()
        
        return {
            'available': True,
            'message': f'Available at {processor.pmtiles_binary}',
            'binary_path': str(processor.pmtiles_binary)
        }
        
    except Exception as e:
        return {
            'available': False,
            'message': str(e),
            'binary_path': None
        }


def validate_zoom_levels(min_z: int, max_z: int):
    """Validate zoom level range with detailed messages"""
    if not (0 <= min_z <= 22):
        raise ValueError(f"min_z must be between 0 and 22, got {min_z}")
    
    if not (0 <= max_z <= 22):
        raise ValueError(f"max_z must be between 0 and 22, got {max_z}")
    
    if max_z < min_z:
        raise ValueError(f"max_z ({max_z}) must be >= min_z ({min_z})")
    
    # Warnings for large ranges
    zoom_range = max_z - min_z + 1
    if zoom_range > 10:
        print(f"Warning: Large zoom range ({zoom_range} levels) will generate many tiles and may take significant time")
    
    if zoom_range > 15:
        print(f"Consider reducing the zoom range or using more workers for better performance")


def ensure_output_dir(output_path: Path, force: bool = False):
    """Ensure output directory/file path is valid with enhanced checks"""
    if output_path.suffix.lower() in ['.mbtiles', '.pmtiles']:
        # File output - check parent directory and file existence
        parent = output_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            if not force:
                raise FileExistsError(
                    f"Output file already exists: {output_path}\n"
                    f"Use --force to overwrite"
                )
            else:
                output_path.unlink()
                print(f"Removed existing file: {output_path}")
    else:
        # Directory output
        if output_path.exists():
            if not output_path.is_dir():
                raise ValueError(f"Output path exists but is not a directory: {output_path}")
            
            if not force:
                # Check if directory has content
                if any(output_path.iterdir()):
                    raise FileExistsError(
                        f"Output directory already exists and is not empty: {output_path}\n"
                        f"Use --force to overwrite"
                    )
            else:
                shutil.rmtree(output_path)
                print(f"Removed existing directory: {output_path}")
        
        output_path.mkdir(parents=True, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def estimate_processing_time(zoom_range: int, workers: int = 4) -> str:
    """Rough estimate of processing time based on zoom range"""
    # Very rough estimates based on typical performance
    base_time_minutes = zoom_range * 2  # 2 minutes per zoom level base
    parallel_factor = min(workers / 4, 1.0)  # 4 workers is baseline
    
    estimated_minutes = base_time_minutes / parallel_factor
    
    if estimated_minutes < 60:
        return f"~{int(estimated_minutes)} minutes"
    else:
        hours = estimated_minutes / 60
        return f"~{hours:.1f} hours"