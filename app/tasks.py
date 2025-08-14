from celery import Celery
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app import models
import random
from datetime import datetime, timedelta
import time

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
        time.sleep(5)
        # Generate dummy result
        dummy_result = create_dummy_result(request_id, request.vendor, request.tracking_number)
        
        # Save result to database
        db_result = models.Result(
            request_id=request_id,
            sender=dummy_result["sender"],
            receiver=dummy_result["receiver"],
            parcel_current_status=dummy_result["status"],
            events=dummy_result["events"]
        )
        db.add(db_result)
        
        # Update request status to completed
        request.status = "completed"
        db.commit()
        
        return f"Successfully processed request {request_id}"
    
    except Exception as e:
        # Update status to failed
        if request:
            request.status = "failed"
            db.commit()
        return f"Failed to process request {request_id}: {str(e)}"
    finally:
        db.close()

def create_dummy_result(request_id: int, vendor: str, tracking_number: str):
    senders = ["John Doe", "ABC Company", "Sarah Ahmed", "Tech Store BD"]
    receivers = ["Jane Smith", "XYZ Corp", "Rahman Khan", "Customer Care"]
    statuses = ["In Transit", "Out for Delivery", "Delivered", "At Local Hub"]
    locations = ["Dhaka Hub", "Chittagong Port", "Sylhet Branch", "Rajshahi Center", None]
    
    # Generate 3-5 events
    num_events = random.randint(3, 5)
    events = []
    base_time = datetime.now() - timedelta(days=2)
    
    event_comments = [
        "Package picked up from sender",
        "Package arrived at sorting facility", 
        "In transit to destination",
        "Out for delivery",
        "Package delivered successfully"
    ]
    
    for i in range(num_events):
        event_time = base_time + timedelta(hours=i*8 + random.randint(0, 4))
        events.append({
            "datetime": event_time.isoformat(),
            "comment": event_comments[min(i, len(event_comments)-1)],
            "location": random.choice(locations)
        })
    
    return {
        "sender": random.choice(senders),
        "receiver": random.choice(receivers), 
        "status": random.choice(statuses),
        "events": events
    }