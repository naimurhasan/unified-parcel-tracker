import httpx
from typing import List
from datetime import datetime
from .base import VendorTracker, TrackingResult, TrackingEvent

class SteadfastTracker(VendorTracker):
    
    @property
    def vendor_name(self) -> str:
        return "STEADFAST"
    
    @property
    def api_endpoints(self) -> List[str]:
        return ["https://steadfast.com.bd/track/consignment/{tracking_id}"]
    
    def validate_tracking_number(self, tracking_number: str) -> bool:
        return len(tracking_number) >= 15 and tracking_number.isalnum()
    
    async def track_package(self, tracking_number: str) -> TrackingResult:
        async with httpx.AsyncClient() as client:
            url = f"https://steadfast.com.bd/track/consignment/{tracking_number}"
            response = await client.get(url)
            data = response.json()
            
            events = []
            current_status = "unknown"
            sender = None
            receiver = None
            
            if data.get("status") == 1 and "result" in data:
                result = data["result"]
                receiver = result.get("cus_name")
                current_status = self._map_status(result.get("status", 0))
                
                # Process tracking events
                for tracking in data.get("trackings", []):
                    events.append(TrackingEvent(
                        datetime=datetime.fromisoformat(tracking["created_at"].replace('Z', '+00:00')),
                        status=tracking.get("text", ""),
                        description=tracking.get("text", ""),
                        location=None  # Extract from deliveryman info if needed
                    ))
            
            return TrackingResult(
                tracking_number=tracking_number,
                current_status=current_status,
                sender=sender,
                receiver=receiver,
                events=events
            )
    
    def _map_status(self, status_code: int) -> str:
        status_map = {
            1: "pending",
            2: "delivered", 
            3: "cancelled",
            # Add more mappings as needed
        }
        return status_map.get(status_code, "unknown")