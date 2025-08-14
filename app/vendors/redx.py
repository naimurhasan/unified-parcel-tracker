import httpx
from typing import List
from datetime import datetime
from .base import VendorTracker, TrackingResult, TrackingEvent

class RedxTracker(VendorTracker):
    
    @property
    def vendor_name(self) -> str:
        return "REDX"
    
    @property
    def api_endpoints(self) -> List[str]:
        return [
            "https://api.redx.com.bd/parcel-track/{tracking_id}",
            "https://api.redx.com.bd/v1/logistics/global-tracking/{tracking_id}"
        ]
    
    def validate_tracking_number(self, tracking_number: str) -> bool:
        # REDX format validation
        return len(tracking_number) >= 10 and tracking_number.isalnum()
    
    async def track_package(self, tracking_number: str) -> TrackingResult:
        async with httpx.AsyncClient() as client:
            # Get basic parcel info
            parcel_url = f"https://api.redx.com.bd/parcel-track/{tracking_number}"
            parcel_response = await client.get(parcel_url)
            parcel_data = parcel_response.json()
            
            # Get tracking events
            tracking_url = f"https://api.redx.com.bd/v1/logistics/global-tracking/{tracking_number}"
            tracking_response = await client.get(tracking_url)
            tracking_data = tracking_response.json()
            
            events = []
            if not tracking_data.get("isError") and "tracking" in tracking_data:
                for event in tracking_data["tracking"]:
                    events.append(TrackingEvent(
                        datetime=datetime.fromisoformat(event["time"].replace('Z', '+00:00')),
                        status=event["status"],
                        description=event["messageEn"],
                        location=None
                    ))
            
            current_status = "unknown"
            sender = None
            receiver = None
            
            if not parcel_data.get("isError") and "parcel" in parcel_data:
                current_status = parcel_data["parcel"].get("STATUS", "unknown")
                receiver = parcel_data["parcel"].get("CUSTOMER_NAME")
            
            return TrackingResult(
                tracking_number=tracking_number,
                current_status=current_status,
                sender=sender,
                receiver=receiver,
                events=events
            )