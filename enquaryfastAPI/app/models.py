from sqlalchemy import Column, String, Integer, Boolean, DateTime, SmallInteger, Text
from app.database import Base
import datetime

class Client(Base):
    __tablename__ = "Clients"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(1), nullable=False)
    yearOfBirth = Column(Integer, nullable=False)
    mobileNo = Column(String(15), nullable=False)
    email = Column(String(100))
    note = Column(String(200))
    isActive = Column(Boolean, nullable=False)
    addedOn = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    modifiedOn = Column(DateTime)
    isVerified = Column(Boolean, nullable=False, default=False)
    idProofType = Column(String(1))
    proofNo = Column(String(50))
    loginid = Column(String(36), nullable=False)

class Enquiry(Base):
    __tablename__ = "Enquiry"
    
    id = Column(String, primary_key=True)
    customer_id = Column(String)
    customer_email = Column(String)
    service_id = Column(String)
    title = Column(String)
    description = Column(Text)
    current_status = Column(String)
    sales_person_name = Column(String)
    sales_rep_id = Column(String)
    submission_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class EnquiryHistory(Base):
    __tablename__ = "enquiry_history"
    
    id = Column(String, primary_key=True)
    enquiry_id = Column(String)
    notes = Column(Text)
    status = Column(String)
    update_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    updated_by_user_id = Column(String)

class Service(Base):
    __tablename__ = "Services"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category = Column(String(100))
    status = Column(String(1), nullable=False)
    parentId = Column(String(36))
    createdAt = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updatedAt = Column(DateTime)
    clickCount = Column(Integer, nullable=False, default=0)
    rating = Column(Integer, nullable=False, default=0)
    isFeatured = Column(Boolean, nullable=False, default=False)
    iconImagePath = Column(String(100))
    bannerImagePath = Column(String(100))
    ord = Column(SmallInteger, nullable=False)