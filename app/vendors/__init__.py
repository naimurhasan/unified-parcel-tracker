from .registry import vendor_registry
from .redx import RedxTracker

# Auto-register all vendors
vendor_registry.register(RedxTracker)

__all__ = ['vendor_registry']