from .registry import vendor_registry
from .redx import RedxTracker
from .bpo import BpoTracker
from .steadfast import SteadfastTracker
from .sundarban import SundarbanTracker

# Auto-register all vendors
vendor_registry.register(RedxTracker)
vendor_registry.register(BpoTracker)
vendor_registry.register(SteadfastTracker)
vendor_registry.register(SundarbanTracker)

__all__ = ['vendor_registry']