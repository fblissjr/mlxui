"""
Core module for the mlxui backend.
This __init__.py makes 'core' a Python package and explicitly re-exports
key components for easier access from other parts of the backend.
"""
from .mlx_adapter import MLXAdapter, get_mlx_adapter
__all__ = ["MLXAdapter", "get_mlx_adapter"]