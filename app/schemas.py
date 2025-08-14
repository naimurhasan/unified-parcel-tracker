from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TrackingRequest(BaseModel):
    vendor: str
    tracking_number: str

class RequestResponse(BaseModel):
    id: int
    vendor: str
    tracking_number: str
    status: str
    created_at: datetime

class EventData(BaseModel):
    datetime: str
    comment: str
    location: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    event_datetime: datetime
    comment: str
    location: Optional[str] = None

class ResultResponse(BaseModel):
    id: int
    request_id: int
    sender: str
    receiver: str
    parcel_current_status: str
    events: List[EventResponse]
    created_at: datetime

    class Config:
        from_attributes = True