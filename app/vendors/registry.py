from typing import Dict, Type, List
from .base import VendorTracker

class VendorRegistry:
    """Registry to manage all vendor implementations"""
    
    def __init__(self):
        self._vendors: Dict[str, Type[VendorTracker]] = {}
    
    def register(self, vendor_class: Type[VendorTracker]):
        """Register a vendor implementation"""
        vendor_instance = vendor_class()
        self._vendors[vendor_instance.vendor_name.upper()] = vendor_class
    
    def get_vendor(self, vendor_name: str) -> VendorTracker:
        """Get vendor tracker instance"""
        vendor_class = self._vendors.get(vendor_name.upper())
        if not vendor_class:
            raise ValueError(f"Vendor '{vendor_name}' not supported")
        return vendor_class()
    
    def list_vendors(self) -> List[str]:
        """Get list of supported vendors"""
        return list(self._vendors.keys())
    
    def is_supported(self, vendor_name: str) -> bool:
        """Check if vendor is supported"""
        return vendor_name.upper() in self._vendors

# Global registry instance
vendor_registry = VendorRegistry()