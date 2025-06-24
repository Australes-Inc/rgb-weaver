# rgbweaver/core/processors/base.py
"""
Base processor class and result types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ProcessResult:
    """Result of a processing operation"""
    success: bool
    output_path: Path
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    temp_files: Optional[list] = None


class ProcessorBase(ABC):
    """Base class for all processors"""
    
    @abstractmethod
    def process(self, dem_path: Path, output_path: Path, **kwargs) -> ProcessResult:
        """Process DEM to specified output format"""
        pass
    
    def cleanup_temp_files(self, temp_files: list):
        """Clean up temporary files"""
        for temp_file in temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")