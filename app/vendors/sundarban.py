import httpx
from datetime import datetime
from .base import VendorTracker, TrackingResult, TrackingEvent
import json

class SundarbanTracker(VendorTracker):
    
    @property
    def vendor_name(self) -> str:
        return "Sundarban"
    
    @property
    def api_endpoints(self) -> list[str]:
        return ["https://tracking.sundarbancourierltd.com/Home/getDatabyCN"]
    
    def validate_tracking_number(self, tracking_number: str) -> bool:
        return len(tracking_number) >= 10 and tracking_number.isdigit()
    
    async def track_package(self, tracking_number: str) -> TrackingResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://tracking.sundarbancourierltd.com/Home/getDatabyCN"
            
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.6',
                'Cache-Control': 'no-cache',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://tracking.sundarbancourierltd.com',
                'Referer': 'https://tracking.sundarbancourierltd.com/',
                'Pragma': 'no-cache',
                'Sec-CH-UA': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-GPC': '1',
                'Key': 'CzbZcWnwf7TNTzluD9rxyXCUqzN4xOhs'
            }
            
            # JSON payload instead of form data
            json_data = {
                'selectedtypes': 'cnno',
                'selectedtimes': '30',
                'inputvalue': tracking_number
            }
            
            try:
                response = await client.post(url, json=json_data, headers=headers)
                print(f"Sundarban API response status: {response.status_code}")
                print(f"Sundarban API response text: {response.text[:200]}...")  # Debug log
                
                # Check if response is empty or not JSON
                if not response.text.strip():
                    print(f"Empty response from Sundarban API for tracking: {tracking_number}")
                    return self._create_empty_result(tracking_number, "No data found")
                
                # Try to parse JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError as je:
                    print(f"JSON decode error for Sundarban: {je}")
                    print(f"Raw response: {response.text}")
                    return self._create_empty_result(tracking_number, "Invalid response format")
                
                return self._process_sundarban_data(response_data, tracking_number)
                
            except httpx.TimeoutException:
                print(f"Timeout error for Sundarban tracking: {tracking_number}")
                return self._create_empty_result(tracking_number, "API timeout")
            
            except Exception as e:
                print(f"Unexpected error for Sundarban tracking {tracking_number}: {str(e)}")
                return self._create_empty_result(tracking_number, f"API error: {str(e)}")
    
    def _process_sundarban_data(self, response_data, tracking_number):
        """Process successful Sundarban API response"""
        events = []
        current_status = "unknown"
        sender = None
        receiver = None
        
        if response_data and isinstance(response_data, list) and len(response_data) > 0:
            package_info = response_data[0]
            
            current_status = package_info.get("status", "unknown")
            sender = package_info.get("sender")
            receiver = package_info.get("receiver")
            
            # Get receiver contact if receiver name is not available
            if not receiver and package_info.get("receiverContact"):
                receiver = f"Contact: {package_info.get('receiverContact')}"
            
            # Process status list (events)
            status_list = package_info.get("cnStatusList", [])
            for status_item in status_list:
                try:
                    status_date = status_item.get("statusDate")
                    if status_date:
                        # Handle datetime format (ISO format with T)
                        if 'T' in status_date:
                            event_datetime = datetime.fromisoformat(status_date.replace('T', ' ').rstrip('Z'))
                        else:
                            event_datetime = datetime.fromisoformat(status_date)
                    else:
                        event_datetime = datetime.now()
                    
                    # Build location info
                    location_parts = []
                    if status_item.get("fromSubBranch"):
                        location_parts.append(f"From: {status_item['fromSubBranch']}")
                    if status_item.get("toSubBranch"):
                        location_parts.append(f"To: {status_item['toSubBranch']}")
                    if status_item.get("downloadSubBranchName"):
                        location_parts.append(status_item['downloadSubBranchName'])
                    
                    location = " | ".join(location_parts) if location_parts else None
                    
                    # Build description
                    description = status_item.get("status", "")
                    if status_item.get("vehicleNo") and status_item["vehicleNo"] not in ["N/A", "null", None]:
                        description += f" (Vehicle: {status_item['vehicleNo']})"
                    if status_item.get("deliveryMan"):
                        description += f" (Delivery: {status_item['deliveryMan']})"
                    if status_item.get("bagNo") and status_item["bagNo"] not in ["null", "Non", None]:
                        description += f" (Bag: {status_item['bagNo']})"
                    
                    events.append(TrackingEvent(
                        datetime=event_datetime,
                        status=status_item.get("status", ""),
                        description=description,
                        location=location
                    ))
                    
                except Exception as e:
                    print(f"Error processing Sundarban event: {e}")
                    continue
            
            # Sort events by datetime
            events.sort(key=lambda x: x.datetime)
            
            # Add booking info if available
            if package_info.get("destBranch") and package_info.get("bookingDate"):
                try:
                    booking_date = datetime.fromisoformat(package_info["bookingDate"].replace('T', ' ').rstrip('Z'))
                    destination_info = f"Destination: {package_info['destBranch']}"
                    if package_info.get("bookingBranch"):
                        destination_info += f" | From: {package_info['bookingBranch']}"
                    
                    # Only add booking event if not already present in cnStatusList
                    if not any("booking complete" in e.description.lower() for e in events):
                        booking_event = TrackingEvent(
                            datetime=booking_date,
                            status="Booked",
                            description=f"Package booked | {destination_info}",
                            location=package_info.get("bookingBranch")
                        )
                        events.insert(0, booking_event)
                except Exception as e:
                    print(f"Error processing booking info: {e}")
        
        return TrackingResult(
            tracking_number=tracking_number,
            current_status=current_status,
            sender=sender,
            receiver=receiver,
            events=events
        )
    
    def _create_empty_result(self, tracking_number: str, reason: str) -> TrackingResult:
        """Create empty result when API fails"""
        return TrackingResult(
            tracking_number=tracking_number,
            current_status=f"Error: {reason}",
            sender=None,
            receiver=None,
            events=[TrackingEvent(
                datetime=datetime.now(),
                status="error",
                description=f"Failed to fetch tracking data: {reason}",
                location=None
            )]
        )