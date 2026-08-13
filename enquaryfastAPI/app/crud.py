from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_
from app.models import Enquiry, EnquiryHistory, Client, Service
from app.schemas import RequestFilter
from datetime import datetime

# --- Client & Service Lookups ---

def get_client(db: Session, client_id: str):
    return db.query(Client).filter(Client.id == client_id).first()

def get_service(db: Session, service_id: str):
    return db.query(Service).filter(Service.id == service_id).first()

# --- Enquiry Lookups ---

def get_enquiry(db: Session, enquiry_id: str):
    return db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()

def get_enquiry_by_id_and_customer(db: Session, enquiry_id: str, customer_id: str):
    return db.query(Enquiry).filter(
        Enquiry.id == enquiry_id, 
        Enquiry.customer_id == customer_id
    ).first()

def get_enquiries_by_customer(db: Session, customer_id: str):
    return db.query(Enquiry).filter(Enquiry.customer_id == customer_id).all()

def get_enquiries_with_service_name_by_customer(db: Session, customer_id: str):
    # Replaces the custom @Query with JOIN[cite: 20]
    return db.query(Enquiry, Service.name).join(
        Service, Enquiry.service_id == Service.id
    ).filter(Enquiry.customer_id == customer_id).all()

def get_overdue_actionable_enquiries(db: Session, threshold: datetime):
    # Replaces findOverdueActionableEnquiries[cite: 20]
    return db.query(Enquiry).filter(
        Enquiry.last_updated < threshold,
        Enquiry.current_status.in_(["NEW", "ASSIGNED", "IN PROGRESS"])
    ).all()

# --- Enquiry History ---

def get_enquiry_history(db: Session, enquiry_id: str):
    # Replaces findByEnquiryIdOrderByUpdateTimestampAsc[cite: 19]
    return db.query(EnquiryHistory).filter(
        EnquiryHistory.enquiry_id == enquiry_id
    ).order_by(asc(EnquiryHistory.update_timestamp)).all()

# --- Admin Dashboard (Dynamic Filtering & Pagination) ---

def get_admin_enquiries(db: Session, status: str = None, assigned_to: str = None, filter_params: RequestFilter = None):
    query = db.query(Enquiry)

    # 1. Apply Status/Assignment Filters[cite: 20]
    if status:
        query = query.filter(Enquiry.current_status == status)
    if assigned_to:
        query = query.filter(Enquiry.sales_rep_id == assigned_to)
        
    # 2. Apply Search Terms if present (e.g. "title:broken;current_status:NEW")
    if filter_params and filter_params.searchTerms:
        pairs = filter_params.searchTerms.split(";")
        for pair in pairs:
            kv = pair.split(":", 1)
            if len(kv) == 2:
                field, value = kv[0].strip(), kv[1].strip()
                if field and value and hasattr(Enquiry, field):
                    column = getattr(Enquiry, field)
                    query = query.filter(column.ilike(f"%{value.lower()}%"))

    # 3. Apply Sorting
    if filter_params:
        sort_column = getattr(Enquiry, filter_params.sortBy if filter_params.sortBy else "submission_date", Enquiry.submission_date)
        if filter_params.sortDescending:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
            
    # 4. Apply Pagination
    total_count = query.count()
    if filter_params:
        page = max(0, filter_params.page - 1)
        query = query.offset(page * filter_params.pageSize).limit(filter_params.pageSize)
        
    return query.all(), total_count