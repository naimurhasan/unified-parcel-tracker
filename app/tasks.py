from celery import Celery
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app import models
from app.vendors import vendor_registry
import asyncio
import random
from datetime import datetime, timedelta

@celery_app.task
def process_pending_requests():
    db = SessionLocal()
    try:
        pending_requests = db.query(models.Request).filter(
            models.Request.status == "pending"
        ).all()
        
        for request in pending_requests:
            process_tracking_request.delay(request.id)
        
        return f"Queued {len(pending_requests)} requests for processing"
    finally:
        db.close()

@celery_app.task
def process_tracking_request(request_id: int):
    """Sync wrapper for async tracking"""
    return asyncio.run(_async_process_tracking_request(request_id))

async def _async_process_tracking_request(request_id: int):
    db = SessionLocal()
    try:
        request = db.query(models.Request).filter(models.Request.id == request_id).first()
        if not request:
            return "Request not found"
        
        # Update status to processing
        request.status = "processing"
        db.commit()
        
        # Simple math operation (as requested)
        result_value = request_id * 7 + 42
        print(f"Processing request {request_id}: {request_id} * 7 + 42 = {result_value}")
        
        # Try vendor plugin first
        if vendor_registry.is_supported(request.vendor):
            tracker = vendor_registry.get_vendor(request.vendor)
            tracking_result = await tracker.track_package(request.tracking_number)
            
            # Save result to database
            db_result = models.Result(
                request_id=request_id,
                sender=tracking_result.sender,
                receiver=tracking_result.receiver,
                parcel_current_status=tracking_result.current_status
            )
            db.add(db_result)
            db.flush()  # Get the ID
            
            # Save events
            for event in tracking_result.events:
                db_event = models.Event(
                    result_id=db_result.id,
                    event_datetime=event.datetime,
                    comment=event.description,
                    location=event.location
                )
                db.add(db_event)
        
        # Update request status to completed
        request.status = "completed"
        db.commit()
        
        return f"Successfully processed request {request_id}"
    
    except Exception as e:
        db.rollback()
        # Update status to failed
        if request:
            request.status = "failed"
            db.commit()
        return f"Failed to process request {request_id}: {str(e)}"
    finally:
        db.close()
