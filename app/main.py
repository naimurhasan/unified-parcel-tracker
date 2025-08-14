from fastapi import FastAPI
from app.database import engine
from app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sunbeam Mail Track", version="1.0.0")

@app.get("/")
async def hello():
    return {"message": "Hello from Sunbeam Mail Track!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}