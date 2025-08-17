from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from .tasks import process_tracking_request

from app.database import engine, get_db
from app import models, schemas
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Unified Parcel Tracker", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# Web Interface Routes
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Serve the main tracking web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# Unified API v1 Routes
@app.post("/api/v1/track", response_model=schemas.RequestResponse)
async def create_tracking_request(
    tracking_req: schemas.TrackingRequest,
    db: Session = Depends(get_db)
):
    """Create a new tracking request"""
    db_request = models.Request(
        vendor=tracking_req.vendor,
        tracking_number=tracking_req.tracking_number
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/api/v1/requests", response_model=List[schemas.RequestResponse])
async def get_all_requests(
    status: str = None,
    vendor: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all tracking requests with optional filtering by status and vendor"""
    query = db.query(models.Request)
    
    if status:
        query = query.filter(models.Request.status == status)
    if vendor:
        query = query.filter(models.Request.vendor.ilike(f"%{vendor}%"))
    
    requests = query.order_by(models.Request.created_at.desc()).limit(limit).all()
    return requests

@app.get("/api/v1/results/{request_id}", response_model=schemas.ResultResponse)
async def get_result_details(request_id: int, db: Session = Depends(get_db)):
    """Get detailed tracking result including all events for a specific request"""
    result = db.query(models.Result).filter(models.Result.request_id == request_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found for this request")
    return result

@app.get("/api/v1/track/{tracking_number}")
async def get_tracking_by_number(tracking_number: str, db: Session = Depends(get_db)):
    """Search for tracking result by tracking number across all vendors"""
    # Find the request first
    request = db.query(models.Request).filter(
        models.Request.tracking_number == tracking_number
    ).order_by(models.Request.created_at.desc()).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Tracking number not found")
    
    # Get the result if it exists
    result = db.query(models.Result).filter(models.Result.request_id == request.id).first()
    
    response = {
        "tracking_number": tracking_number,
        "vendor": request.vendor,
        "request_id": request.id,
        "request_status": request.status,
        "created_at": request.created_at,
        "result": None
    }
    
    if result:
        response["result"] = {
            "id": result.id,
            "sender": result.sender,
            "receiver": result.receiver,
            "current_status": result.parcel_current_status,
            "events": [
                {
                    "id": event.id,
                    "datetime": event.event_datetime,
                    "comment": event.comment,
                    "location": event.location
                }
                for event in result.events
            ],
            "created_at": result.created_at
        }
    
    return response

@app.post("/api/v1/process/{request_id}")
async def manual_process(request_id: int, db: Session = Depends(get_db)):
    """Manually trigger processing of a specific request"""
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Trigger manual processing
    task = process_tracking_request.delay(request_id)
    return {"message": "Processing started", "task_id": task.id}