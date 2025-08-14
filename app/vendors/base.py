from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrackingEvent:
    datetime: datetime
    status: str
    description: str
    location: Optional[str] = None

@dataclass
class TrackingResult:
    tracking_number: str
    current_status: str
    sender: Optional[str] = None
    receiver: Optional[str] = None
    events: List[TrackingEvent] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []

class VendorTracker(ABC):
    """Abstract base class for all vendor trackers"""
    
    @property
    @abstractmethod
    def vendor_name(self) -> str:
        """Return vendor name"""
        pass
    
    @abstractmethod
    async def track_package(self, tracking_number: str) -> TrackingResult:
        """Track a package and return structured result"""
        pass
    
    @abstractmethod
    def validate_tracking_number(self, tracking_number: str) -> bool:
        """Validate if tracking number format is correct for this vendor"""
        pass
    
    @property
    def requires_browser(self) -> bool:
        """Whether this vendor requires browser automation (Playwright)"""
        return False
    
    @property
    def api_endpoints(self) -> List[str]:
        """List of API endpoints this vendor uses"""
        return []