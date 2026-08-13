from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app import schemas
from app.services import enquiry as enquiry_service

router = APIRouter(prefix="/enquiryapi/v1/usr/{userId}/enquiries", tags=["Customer Enquiries"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_enquiry(userId: str, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    
    user_id_str = None
    service_id = None
    title = None
    description = None
    
    for key, val in body.items():
        if key.lower() in ("userid", "customerid"):
            user_id_str = str(val)
        elif key.lower() == "serviceid":
            service_id = str(val)
        elif key.lower() == "title":
            title = str(val)
        elif key.lower() in ("description", "message"):
            description = str(val)
            
    if not user_id_str:
        user_id_str = userId
        
    if not user_id_str or not service_id or not description:
        raise HTTPException(status_code=400, detail="Missing required fields (UserId/ServiceId/Description)")
        
    if not title:
        title = "Enquiry"

    enquiry_req = schemas.EnquiryRequest(userId=user_id_str, serviceId=service_id, title=title, description=description)
    data = await enquiry_service.create_enquiry(db, enquiry_req)
    
    return {
        "Success": True,
        "Code": "ENQR.CREATED",
        "Message": "Enquiry created successfully.",
        "Data": data
    }

@router.get("/my-enquiries")
def get_customer_enquiries(userId: str, db: Session = Depends(get_db)):
    data = enquiry_service.find_enquiries_by_customer(db, userId)
    return {
        "Success": True,
        "Code": "ENQR.FOUND",
        "Message": "Enquiries found.",
        "Data": data
    }

@router.get("/{enquiryId}")
def get_enquiry_details(userId: str, enquiryId: str, db: Session = Depends(get_db)):
    data = enquiry_service.get_enquiry_if_owned(db, enquiryId, userId)
    if not data:
        return {
            "Success": False,
            "Code": "ENQR.NOT_FOUND",
            "Message": "Enquiry not found or access denied.",
            "Data": None
        }
    return {
        "Success": True,
        "Code": "ENQR.FOUND",
        "Message": "Enquiry found.",
        "Data": data
    }

@router.patch("/{enquiryId}")
def edit_enquiry_self(userId: str, enquiryId: str, request: schemas.EnquiryRequest, db: Session = Depends(get_db)):
    data = enquiry_service.edit_enquiry_self(db, enquiryId, request)
    return {
        "Success": True,
        "Code": "ENQR.UPDATED",
        "Message": "Enquiry updated successfully.",
        "Data": data
    }

@router.delete("/{enquiryId}")
def delete_enquiry_self(userId: str, enquiryId: str, db: Session = Depends(get_db)):
    enquiry_service.delete_enquiry_self(db, enquiryId, userId)
    return {
        "Success": True,
        "Code": "ENQR.DELETED",
        "Message": "Enquiry deleted successfully.",
        "Data": None
    }

@router.get("/{enquiryId}/history")
def view_enquiry_history_self(userId: str, enquiryId: str, db: Session = Depends(get_db)):
    data = enquiry_service.get_enquiry_history_if_owned(db, enquiryId, userId)
    return {
        "Success": True,
        "Code": "ENQR.HISTORY_FOUND",
        "Message": "Enquiry history found.",
        "Data": data
    }