import httpx
from datetime import datetime
from .base import VendorTracker, TrackingResult, TrackingEvent

class BpoTracker(VendorTracker):
    
    @property
    def vendor_name(self) -> str:
        return "BPO"
    
    @property
    def api_endpoints(self) -> list[str]:
        return ["https://t.bpodms.gov.bd/get_events?item_id={tracking_id}"]
    
    def validate_tracking_number(self, tracking_number: str) -> bool:
        # BPO format: typically starts with letters followed by numbers and ends with BD
        # Example: DL636643547BD
        return (len(tracking_number) >= 10 and 
                tracking_number.endswith('BD') and 
                any(c.isalpha() for c in tracking_number) and
                any(c.isdigit() for c in tracking_number))
    
    async def track_package(self, tracking_number: str) -> TrackingResult:
        async with httpx.AsyncClient() as client:
            url = f"https://t.bpodms.gov.bd/get_events?item_id={tracking_number}"
            response = await client.get(url)
            data = response.json()
            
            events = []
            current_status = "unknown"
            sender = None
            receiver = None
            
            if "events" in data and data["events"]:
                # Process events (BPO events are in chronological order)
                for event_data in data["events"]:
                    # Combine date and time
                    event_datetime_str = f"{event_data['date']} {event_data['time']}"
                    try:
                        # Parse BPO datetime format: "2025-01-03 09:22:37 PM"
                        event_datetime = datetime.strptime(event_datetime_str, "%Y-%m-%d %I:%M:%S %p")
                    except ValueError:
                        # Fallback to just date if time parsing fails
                        event_datetime = datetime.strptime(event_data['date'], "%Y-%m-%d")
                    
                    events.append(TrackingEvent(
                        datetime=event_datetime,
                        status=event_data.get("status", ""),
                        description=event_data.get("description", ""),
                        location=event_data.get("branch", "")
                    ))
                
                # Get current status from latest event
                if events:
                    current_status = events[-1].status
            
            return TrackingResult(
                tracking_number=tracking_number,
                current_status=current_status,
                sender=sender,  # BPO API doesn't provide sender info
                receiver=receiver,  # BPO API doesn't provide receiver info
                events=events
            )