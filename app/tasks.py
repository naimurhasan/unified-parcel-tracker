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
        
        request.status = "processing"
        db.commit()
        
        result_value = request_id * 7 + 42
        print(f"Processing request {request_id}: {request_id} * 7 + 42 = {result_value}")
        
        # Try vendor plugin first
        if vendor_registry.is_supported(request.vendor):
            try:
                tracker = vendor_registry.get_vendor(request.vendor)
                tracking_result = await tracker.track_package(request.tracking_number)

                is_error_result = (
                    "API Error:" in tracking_result.current_status or
                    "error" in tracking_result.current_status.lower() or
                    tracking_result.current_status == "unknown" or
                    len(tracking_result.events) == 0 or
                    (len(tracking_result.events) == 1 and "failed to fetch" in tracking_result.events[0].description.lower())
                )
                
                # Save result to database
                db_result = models.Result(
                    request_id=request_id,
                    sender=tracking_result.sender,
                    receiver=tracking_result.receiver,
                    parcel_current_status=tracking_result.current_status
                )
                db.add(db_result)
                db.flush()
                
                # Save events
                for event in tracking_result.events:
                    db_event = models.Event(
                        result_id=db_result.id,
                        event_datetime=event.datetime,
                        comment=event.description,
                        location=event.location
                    )
                    db.add(db_event)
                
                print(f"Successfully processed {request.vendor} with {len(tracking_result.events)} events")
                
            except Exception as vendor_error:
                print(f"Vendor plugin error for {request.vendor}: {str(vendor_error)}")
                # Create error result instead of failing completely
                db_result = models.Result(
                    request_id=request_id,
                    sender=None,
                    receiver=None,
                    parcel_current_status=f"Error: {str(vendor_error)[:100]}"
                )
                db.add(db_result)
                db.flush()
                
                # Add error event
                db_event = models.Event(
                    result_id=db_result.id,
                    event_datetime=datetime.now(),
                    comment=f"Failed to fetch from {request.vendor} API: {str(vendor_error)[:200]}",
                    location=None
                )
                db.add(db_event)
        
        if is_error_result:
            request.status = "failed"
            print(f"Marking request {request_id} as failed - no valid tracking data from {request.vendor}")
        else:
            request.status = "completed"
            print(f"Successfully processed {request.vendor} with {len(tracking_result.events)} events")
        db.commit()
        
        return f"Successfully processed request {request_id}"
    
    except Exception as e:
        db.rollback()
        print(f"Error processing request {request_id}: {str(e)}")
        if request:
            request.status = "failed"
            db.commit()
        raise

    finally:
        db.close()