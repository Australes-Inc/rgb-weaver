# rgbweaver/core/__init__.py (mise à jour)
"""
Enhanced core components for rgb-weaver Phase 2
"""

from .pipeline import Pipeline, TempFileManager
from .processors import ProcessorFactory, ProcessorBase, ProcessResult
from .outputs import OutputType, OutputFactory

__all__ = [
    'Pipeline', 
    'TempFileManager',
    'ProcessorFactory', 
    'ProcessorBase', 
    'ProcessResult',
    'OutputType', 
    'OutputFactory'
]