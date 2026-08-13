from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database import get_db
from app import schemas
from app.services import enquiry as enquiry_service

router = APIRouter(prefix="/enquiryapi/v1/adm/enquiries", tags=["Admin Enquiries"])
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"

@router.get("")
def get_enquiry_dashboard(
    status: Optional[str] = None,
    assignedTo: Optional[str] = None,
    sortBy: Optional[str] = "lastUpdated",
    page: int = 1,
    pageSize: int = 10,
    searchTerms: Optional[str] = None,
    sortDescending: bool = False,
    db: Session = Depends(get_db)
):
    filter_params = schemas.RequestFilter(
        page=page,
        pageSize=pageSize,
        searchTerms=searchTerms,
        sortBy=sortBy,
        sortDescending=sortDescending
    )
    paged_result = enquiry_service.find_all_filtered_and_paged(db, status, assignedTo, filter_params)
    return {
        "Success": True,
        "Code": "ENQR.FOUND",
        "Message": "Enquiries found.",
        "Data": paged_result
    }

@router.get("/{enquiryId}")
def get_enquiry_details_any(enquiryId: str, db: Session = Depends(get_db)):
    data = enquiry_service.get_enquiry_by_id(db, enquiryId)
    return {
        "Success": True,
        "Code": "ENQR.FOUND",
        "Message": "Enquiry found.",
        "Data": data
    }

@router.delete("/{enquiryId}")
def delete_enquiry_any(enquiryId: str, db: Session = Depends(get_db)):
    enquiry_service.delete_enquiry_by_id(db, enquiryId, ADMIN_USER_ID)
    return {
        "Success": True,
        "Code": "ENQR.DELETED",
        "Message": "Enquiry deleted successfully.",
        "Data": None
    }

@router.patch("/{enquiryId}/status")
async def update_status_and_assignment(enquiryId: str, statusUpdate: schemas.StatusUpdateRequest, db: Session = Depends(get_db)):
    data = await enquiry_service.update_enquiry_status(db, enquiryId, statusUpdate, ADMIN_USER_ID)
    return {
        "Success": True,
        "Code": "ENQR.UPDATED",
        "Message": "Enquiry status updated successfully.",
        "Data": data
    }

@router.patch("/{enquiryId}/comment")
def update_comment_only(enquiryId: str, request: schemas.CommentRequest, db: Session = Depends(get_db)):
    data = enquiry_service.log_comment_only(db, enquiryId, request.comment, ADMIN_USER_ID)
    return {
        "Success": True,
        "Code": "ENQR.UPDATED",
        "Message": "Enquiry comment updated successfully.",
        "Data": data
    }

@router.get("/{enquiryId}/history")
def view_enquiry_history_any(enquiryId: str, db: Session = Depends(get_db)):
    data = enquiry_service.get_enquiry_history_by_id(db, enquiryId)
    return {
        "Success": True,
        "Code": "ENQR.HISTORY_FOUND",
        "Message": "Enquiry history found.",
        "Data": data
    }