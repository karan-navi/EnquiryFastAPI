from datetime import datetime, timedelta
from app.database import SessionLocal
from app.config import settings
from app import crud
from app.services.notification import notification_service

async def send_assignment_reminders():
    # A standalone DB session is required because this runs outside of FastAPI's request cycle
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() - timedelta(hours=settings.enquiry_reminder_threshold_hours)
        overdue_enquiries = crud.get_overdue_actionable_enquiries(db, threshold)
        
        if not overdue_enquiries:
            return

        print(f"Found {len(overdue_enquiries)} overdue enquiries. Sending reminders...")
        
        for enquiry in overdue_enquiries:
            recipient = _get_recipient_email(enquiry)
            subject = _get_reminder_subject(enquiry)
            body = _get_reminder_body(enquiry)
            
            await notification_service.send_direct_notification(recipient, subject, body)
            
    finally:
        db.close()

def _get_recipient_email(enquiry):
    if enquiry.sales_rep_id:
        return f"sales_rep_{enquiry.id}@example.com"
    elif enquiry.sales_person_name:
        return "admin_triage@example.com"
    else:
        return "admin_triage@example.com"

def _get_reminder_subject(enquiry):
    assignee = enquiry.sales_person_name if enquiry.sales_person_name else "Triage Team"
    return f"REMINDER: Enquiry #{enquiry.id} ({assignee}) is Stale!"

def _get_reminder_body(enquiry):
    return (
        f"Enquiry #{enquiry.id} ('{enquiry.title}') has been in status '{enquiry.current_status}' "
        f"since {enquiry.last_updated} and requires your action. "
        f"Please log in and update the status or provide comments."
    )