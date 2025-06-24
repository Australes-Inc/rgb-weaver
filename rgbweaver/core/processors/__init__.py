# rgbweaver/core/processors/__init__.py
"""
Processing components
"""

from .factory import ProcessorFactory
from .base import ProcessorBase, ProcessResult

__all__ = ['ProcessorFactory', 'ProcessorBase', 'ProcessResult']