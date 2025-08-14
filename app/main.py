from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, get_db
from app import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sunbeam Mail Track", version="1.0.0")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/track", response_model=schemas.RequestResponse)
async def create_tracking_request(
    tracking_req: schemas.TrackingRequest,
    db: Session = Depends(get_db)
):
    db_request = models.Request(
        vendor=tracking_req.vendor,
        tracking_number=tracking_req.tracking_number
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/requests", response_model=List[schemas.RequestResponse])
async def get_requests(db: Session = Depends(get_db)):
    return db.query(models.Request).order_by(models.Request.created_at.desc()).limit(10).all()

@app.get("/results/{request_id}", response_model=schemas.ResultResponse)
async def get_result(request_id: int, db: Session = Depends(get_db)):
    result = db.query(models.Result).filter(models.Result.request_id == request_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}