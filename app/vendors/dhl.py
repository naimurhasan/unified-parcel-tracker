from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from datetime import datetime
import json
from .base import VendorTracker, TrackingResult, TrackingEvent

class DhlTracker(VendorTracker):
    
    @property
    def vendor_name(self) -> str:
        return "DHL"
    
    @property
    def requires_browser(self) -> bool:
        return True
    
    @property
    def api_endpoints(self) -> list[str]:
        return ["https://www.dhl.com/utapi"]
    
    def validate_tracking_number(self, tracking_number: str) -> bool:
        # DHL tracking numbers are typically 10-11 digits
        # Examples: 6761952853, 1234567890
        return (len(tracking_number) >= 10 and 
                len(tracking_number) <= 11 and 
                tracking_number.isdigit())
    
    async def track_package(self, tracking_number: str) -> TrackingResult:
        tracking_data = None
        
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            target_url_prefix = f"https://www.dhl.com/utapi?trackingNumber={tracking_number}"

            async def handle_response(response):
                nonlocal tracking_data
                if response.url.startswith(target_url_prefix) and response.status == 200:
                    try:
                        tracking_data = await response.json()
                    except Exception:
                        pass  # Ignore JSON parsing errors

            page.on("response", handle_response)

            # Navigate to DHL tracking page
            tracking_url = f"https://www.dhl.com/bd-en/home/tracking.html?tracking-id={tracking_number}&submit=1&inputsource=marketingstage"
            await page.goto(tracking_url)
            await page.wait_for_timeout(10000)  # Wait for network activity
            
            await browser.close()

        # Parse the tracking data
        if tracking_data and "shipments" in tracking_data and len(tracking_data["shipments"]) > 0:
            return self._parse_tracking_data(tracking_data)
        else:
            # Return empty result if no data found
            return TrackingResult(
                tracking_number=tracking_number,
                current_status="unknown",
                sender=None,
                receiver=None,
                events=[]
            )

    def _parse_tracking_data(self, json_data: dict) -> TrackingResult:
        """Parse DHL tracking JSON data into TrackingResult"""
        shipment = json_data["shipments"][0]
        
        tracking_number = shipment["id"]
        current_status = shipment["status"]["description"]
        
        # Extract sender and receiver information
        sender = None
        receiver = None
        
        if "details" in shipment:
            details = shipment["details"]
            if "shipper" in details and "address" in details["shipper"]:
                sender = details["shipper"]["address"].get("countryCode")
            if "consignee" in details and "address" in details["consignee"]:
                receiver = details["consignee"]["address"].get("countryCode")
        
        # Parse tracking events
        events = []
        if "events" in shipment:
            for event in shipment["events"]:
                # Parse timestamp
                event_datetime = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                
                status = event["status"]
                description = event["description"]
                
                # Extract location information
                location = None
                if "location" in event and "address" in event["location"]:
                    location = event["location"]["address"].get("addressLocality")
                
                events.append(TrackingEvent(
                    datetime=event_datetime,
                    status=status,
                    description=description,
                    location=location
                ))
        
        return TrackingResult(
            tracking_number=tracking_number,
            current_status=current_status,
            sender=sender,
            receiver=receiver,
            events=events
        )
