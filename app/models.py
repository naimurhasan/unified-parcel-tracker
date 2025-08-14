from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String, nullable=False)
    tracking_number = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    result = relationship("Result", back_populates="request", uselist=False)

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"))
    sender = Column(String, nullable=True)
    receiver = Column(String, nullable=True)
    parcel_current_status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    request = relationship("Request", back_populates="result")
    events = relationship("Event", back_populates="result", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("results.id"))
    event_datetime = Column(DateTime, nullable=False)
    comment = Column(String, nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    result = relationship("Result", back_populates="events")