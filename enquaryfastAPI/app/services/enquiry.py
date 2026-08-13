import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import crud, models, schemas
from app.services.notification import notification_service

STATUS_NEW = "NEW"
STATUS_RESOLVED = "RESOLVED"

async def create_enquiry(db: Session, request: schemas.EnquiryRequest) -> schemas.EnquiryResponse:
    enquiry_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    enquiry = models.Enquiry(
        id=enquiry_id,
        customer_id=request.userId,
        customer_email=f"customer_{request.userId}@dummy.com",
        service_id=request.serviceId,
        title=request.title,
        description=request.description,
        current_status=STATUS_NEW,
        submission_date=now,
        last_updated=now
    )
    db.add(enquiry)
    
    history = models.EnquiryHistory(
        id=str(uuid.uuid4()),
        enquiry_id=enquiry_id,
        status=STATUS_NEW,
        notes="Initial submission by customer.",
        updated_by_user_id=request.userId,
        update_timestamp=now
    )
    db.add(history)
    db.commit()
    db.refresh(enquiry)
    db.refresh(history)

    await notification_service.notify_status_change(enquiry, history)
    
    event_data = {
        "Service": enquiry.service_id,
        "title": enquiry.title
    }
    await notification_service.send_event_notification(
        enquiry.customer_id, "C", "CLIENT_ENQUIRY", event_data
    )
    
    return _map_to_response(db, enquiry)

def find_enquiries_by_customer(db: Session, customer_id: str):
    enquiries_services = crud.get_enquiries_with_service_name_by_customer(db, customer_id)
    result = []
    for enquiry, service_name in enquiries_services:
        result.append({
            "enquiry": _map_to_response(db, enquiry).model_dump(),
            "serviceName": service_name
        })
    return result

def find_all_filtered_and_paged(db: Session, req_status: str, assigned_to: str, filter_params: schemas.RequestFilter):
    enquiries, total_count = crud.get_admin_enquiries(db, req_status, assigned_to, filter_params)
    
    enriched_data = []
    for enquiry in enquiries:
        client = crud.get_client(db, enquiry.customer_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        
        service = crud.get_service(db, enquiry.service_id)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        
        timeline = crud.get_enquiry_history(db, enquiry.id)
        
        data = {
            "enquiry": _map_to_response(db, enquiry).model_dump(),
            "customerName": client.name,
            "phone": client.mobileNo,
            "serviceName": service.name,
            "timeline": [schemas.EnquiryHistorySchema.model_validate(h).model_dump() for h in timeline]
        }
        enriched_data.append(data)
        
    return schemas.PagedResult(
        items=enriched_data,
        totalCount=total_count,
        page=filter_params.page if filter_params else 1,
        pageSize=filter_params.pageSize if filter_params else len(enriched_data)
    )

def get_enquiry_if_owned(db: Session, enquiry_id: str, customer_id: str):
    enquiry = crud.get_enquiry_by_id_and_customer(db, enquiry_id, customer_id)
    if enquiry:
        return _map_to_response(db, enquiry)
    return None

def get_enquiry_by_id(db: Session, enquiry_id: str):
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found.")
    return _map_to_response(db, enquiry)

def edit_enquiry_self(db: Session, enquiry_id: str, request: schemas.EnquiryRequest):
    enquiry = crud.get_enquiry_by_id_and_customer(db, enquiry_id, request.userId)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found or access denied.")
    
    if enquiry.current_status != STATUS_NEW:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enquiry can only be edited when status is NEW.")
    
    enquiry.title = request.title
    enquiry.description = request.description
    enquiry.last_updated = datetime.utcnow()
    
    history = models.EnquiryHistory(
        id=str(uuid.uuid4()),
        enquiry_id=enquiry_id,
        status=enquiry.current_status,
        notes=f"Customer edited enquiry details - {request.description}",
        updated_by_user_id=request.userId,
        update_timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    db.refresh(enquiry)
    
    return _map_to_response(db, enquiry)

def delete_enquiry_self(db: Session, enquiry_id: str, customer_id: str):
    enquiry = crud.get_enquiry_by_id_and_customer(db, enquiry_id, customer_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found or access denied.")
    
    if enquiry.current_status != STATUS_NEW:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enquiry can only be deleted when status is NEW.")
    
    history_records = crud.get_enquiry_history(db, enquiry_id)
    for h in history_records:
        db.delete(h)
        
    db.delete(enquiry)
    db.commit()

def delete_enquiry_by_id(db: Session, enquiry_id: str, admin_user_id: str):
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found.")
    
    history = models.EnquiryHistory(
        id=str(uuid.uuid4()),
        enquiry_id=enquiry_id,
        status="DELETED",
        notes="Enquiry deleted - ",
        updated_by_user_id=admin_user_id,
        update_timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    
    history_records = crud.get_enquiry_history(db, enquiry_id)
    for h in history_records:
        db.delete(h)
        
    db.delete(enquiry)
    db.commit()

async def update_enquiry_status(db: Session, enquiry_id: str, update_request: schemas.StatusUpdateRequest, admin_user_id: str):
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry not found with ID: {enquiry_id}")
    
    new_status = update_request.newStatus
    enquiry.current_status = new_status
    enquiry.last_updated = datetime.utcnow()
    
    if update_request.salesPersonName:
        enquiry.sales_person_name = update_request.salesPersonName
    if update_request.salesRepId:
        enquiry.sales_rep_id = update_request.salesRepId
        
    notes = update_request.notes if update_request.notes else f"Status changed - {new_status}"
    history = models.EnquiryHistory(
        id=str(uuid.uuid4()),
        enquiry_id=enquiry_id,
        status=new_status,
        notes=notes,
        updated_by_user_id=admin_user_id,
        update_timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    db.refresh(enquiry)
    db.refresh(history)
    
    await notification_service.notify_status_change(enquiry, history)
    return _map_to_response(db, enquiry)

def log_comment_only(db: Session, enquiry_id: str, comment: str, admin_user_id: str):
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry not found with ID: {enquiry_id}")
    
    history = models.EnquiryHistory(
        id=str(uuid.uuid4()),
        enquiry_id=enquiry_id,
        status=enquiry.current_status,
        notes=comment,
        updated_by_user_id=admin_user_id,
        update_timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    return _map_to_response(db, enquiry)

def get_enquiry_history_if_owned(db: Session, enquiry_id: str, customer_id: str):
    enquiry = crud.get_enquiry_by_id_and_customer(db, enquiry_id, customer_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found or access denied.")
    return [_map_to_response(db, enquiry)]

def get_enquiry_history_by_id(db: Session, enquiry_id: str):
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found.")
    return [_map_to_response(db, enquiry)]

def _map_to_response(db: Session, enquiry: models.Enquiry) -> schemas.EnquiryResponse:
    timeline = crud.get_enquiry_history(db, enquiry.id)
    return schemas.EnquiryResponse(
        id=enquiry.id,
        title=enquiry.title,
        customerId=enquiry.customer_id,
        description=enquiry.description,
        currentStatus=enquiry.current_status,
        submissionDate=enquiry.submission_date,
        timeline=[schemas.EnquiryHistorySchema.model_validate(h) for h in timeline]
    )