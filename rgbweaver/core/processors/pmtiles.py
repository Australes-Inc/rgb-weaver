# rgbweaver/core/processors/pmtiles.py (VERSION AMÉLIORÉE avec binaire bundlé)
"""
PMTiles processor - generates PMTiles from DEM via MBTiles conversion
Uses bundled pmtiles binary for cross-platform compatibility
"""

import os
import platform
from pathlib import Path
from .base import ProcessorBase, ProcessResult
from .mbtiles import MBTilesProcessor
from ...utils import run_command


class PMTilesProcessor(ProcessorBase):
    """
    Processor for PMTiles generation using bundled go-pmtiles binary
    
    Workflow: DEM → MBTiles (temp) → PMTiles (bundled pmtiles convert)
    """
    
    def __init__(self):
        self.pmtiles_binary = self._get_pmtiles_binary()
    
    def _get_pmtiles_binary(self) -> Path:
        """
        Get the path to the bundled pmtiles binary for current platform
        
        Returns:
            Path to pmtiles binary
            
        Raises:
            RuntimeError: If binary not found for current platform
        """
        # Get current platform
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map platform to binary name (only available platforms)
        platform_map = {
            ('windows', 'amd64'): 'pmtiles-windows-x64.exe',
            ('windows', 'x86_64'): 'pmtiles-windows-x64.exe',
            ('linux', 'amd64'): 'pmtiles-linux-x64',
            ('linux', 'x86_64'): 'pmtiles-linux-x64',
            ('darwin', 'amd64'): 'pmtiles-darwin-x64',
            ('darwin', 'x86_64'): 'pmtiles-darwin-x64',
            # Note: darwin_arm64 not available in go-pmtiles releases
        }
        
        # Normalize machine architecture
        if machine in ['amd64', 'x86_64']:
            machine = 'amd64'
        elif machine in ['arm64', 'aarch64']:
            machine = 'arm64'
        
        binary_name = platform_map.get((system, machine))
        
        if not binary_name:
            # Special message for macOS ARM64 users
            if system == 'darwin' and machine == 'arm64':
                raise RuntimeError(
                    f"PMTiles binary not available for macOS Apple Silicon (arm64).\n"
                    f"Workaround options:\n"
                    f"  1. Use MBTiles output: rgb-weaver dem.tif output.mbtiles ...\n"
                    f"  2. Use PNG tiles output: rgb-weaver dem.tif tiles/ ...\n"
                    f"  3. Install go-pmtiles manually and use system PATH\n"
                    f"  4. Use Rosetta 2 to run x64 version (may work)"
                )
            else:
                raise RuntimeError(
                    f"PMTiles binary not available for platform: {system}-{machine}\n"
                    f"Supported platforms: Windows x64, Linux x64, macOS Intel x64\n"
                    f"Please use MBTiles or tiles output instead."
                )
        
        # Get binary path relative to this file
        binary_path = Path(__file__).parent.parent.parent / 'bin' / binary_name
        
        if not binary_path.exists():
            raise RuntimeError(
                f"PMTiles binary not found: {binary_path}\n"
                f"Expected binary: {binary_name}\n"
                f"Please ensure the binary is included in the package."
            )
        
        # Ensure binary is executable on Unix systems
        if system != 'windows':
            os.chmod(binary_path, 0o755)
        
        return binary_path
    
    def process(self, dem_path: Path, output_path: Path, **kwargs) -> ProcessResult:
        """
        Process DEM to PMTiles via MBTiles conversion using bundled binary
        
        Args:
            dem_path: Input DEM path
            output_path: Output PMTiles path (.pmtiles)
            **kwargs: Processing options
            
        Returns:
            ProcessResult with success status and metadata
        """
        temp_manager = kwargs.get('temp_manager')
        verbose = kwargs.get('verbose', False)
        
        if not temp_manager:
            return ProcessResult(
                success=False,
                output_path=output_path,
                error="temp_manager required for PMTiles processing"
            )
        
        temp_files = []
        
        try:
            if verbose:
                print(f"Using PMTiles binary: {self.pmtiles_binary}")
                print("Step 1/2: Generating temporary MBTiles...")
            
            # Step 1: Generate temporary MBTiles
            temp_mbtiles = temp_manager.get_temp_path('.mbtiles')
            temp_files.append(str(temp_mbtiles))
            
            # Use MBTiles processor for initial generation
            mbtiles_processor = MBTilesProcessor()
            mbtiles_result = mbtiles_processor.process(dem_path, temp_mbtiles, **kwargs)
            
            if not mbtiles_result.success:
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error=f"MBTiles generation failed: {mbtiles_result.error}",
                    temp_files=temp_files
                )
            
            if verbose:
                mbtiles_size = temp_mbtiles.stat().st_size / (1024 * 1024)
                print(f"MBTiles generated: {mbtiles_size:.1f} MB")
                print("Step 2/2: Converting MBTiles to PMTiles...")
            
            # Step 2: Convert MBTiles to PMTiles using bundled binary
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build pmtiles convert command with bundled binary
            cmd = [
                str(self.pmtiles_binary),
                'convert',
                str(temp_mbtiles),
                str(output_path)
            ]
            
            # Add optimization options
            if not kwargs.get('deduplication', True):
                cmd.append('--no-deduplication')
            
            # Set custom temp directory if provided
            custom_tmpdir = kwargs.get('tmpdir')
            if custom_tmpdir:
                cmd.extend(['--tmpdir', str(custom_tmpdir)])
            
            # Execute conversion with bundled binary
            result = run_command(cmd, verbose=verbose)
            
            if verbose:
                print("PMTiles conversion completed")
            
            # Verify output file was created
            if not output_path.exists():
                return ProcessResult(
                    success=False,
                    output_path=output_path,
                    error="PMTiles file was not created during conversion",
                    temp_files=temp_files
                )
            
            # Calculate file sizes and compression statistics
            mbtiles_size = temp_mbtiles.stat().st_size if temp_mbtiles.exists() else 0
            pmtiles_size = output_path.stat().st_size
            
            compression_ratio = 0
            if mbtiles_size > 0:
                compression_ratio = (1 - pmtiles_size / mbtiles_size) * 100
            
            # Combine metadata from MBTiles step
            metadata = mbtiles_result.metadata.copy() if mbtiles_result.metadata else {}
            metadata.update({
                'format': 'pmtiles',
                'file_size_bytes': pmtiles_size,
                'file_size_mb': round(pmtiles_size / (1024 * 1024), 2),
                'converted_from': 'mbtiles',
                'compression': 'pmtiles_optimized',
                'temp_mbtiles_size_bytes': mbtiles_size,
                'temp_mbtiles_size_mb': round(mbtiles_size / (1024 * 1024), 2),
                'compression_ratio_percent': round(compression_ratio, 1),
                'pmtiles_binary': str(self.pmtiles_binary),
                'conversion_tool': 'go-pmtiles (bundled)'
            })
            
            if verbose:
                print(f"Final size: {metadata['file_size_mb']} MB")
                if compression_ratio > 0:
                    print(f"Compression: {compression_ratio:.1f}% reduction")
            
            return ProcessResult(
                success=True,
                output_path=output_path,
                metadata=metadata,
                temp_files=temp_files
            )
            
        except Exception as e:
            return ProcessResult(
                success=False,
                output_path=output_path,
                error=f"PMTiles processing failed: {str(e)}",
                temp_files=temp_files
            )