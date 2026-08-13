import httpx
from app.config import settings
from app.models import Enquiry, EnquiryHistory

class NotificationService:
    def __init__(self):
        self.api_url = settings.notificationapi__url

    async def notify_status_change(self, enquiry: Enquiry, new_history: EnquiryHistory):
        # 1. Notify Sales (Triage team)[cite: 23]
        if new_history.status == "NEW":
            await self.send_direct_notification(
                to="triage-team@yourcompany.com",
                subject=f"🔥 New Customer Enquiry Submitted (#{enquiry.id})",
                body=f"A new enquiry has been submitted by customer {enquiry.customer_id}. Status: NEW. Title: {enquiry.title}"
            )

        # 2. Notify Customer (for key status updates)[cite: 23]
        if new_history.status in ["RESOLVED", "AWAITING CUSTOMER"]:
            await self.send_direct_notification(
                to=enquiry.customer_email,
                subject=f"Your Enquiry Status Updated (#{enquiry.id})",
                body=f"Dear Customer,\n\nThe status of your enquiry, '{enquiry.title}', is now: **{new_history.status}**.\n\nAdmin/Sales Notes: {new_history.notes}"
            )

    async def send_direct_notification(self, to: str, subject: str, body: str):
        payload = {
            "recipient": to,
            "subject": subject,
            "body": body,
            "sender": "no-reply@yourcompany.com"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload)
                if response.status_code not in (200, 202):
                    print(f"External notification failed for {to}. Status: {response.status_code}. Response: {response.text}")
                else:
                    print(f"Notification successfully triggered for {to}")
            except Exception as e:
                print(f"Error calling external notification API for {to}: {e}")

    async def send_event_notification(self, user_id: str, user_type: str, event: str, data: dict):
        payload = {
            "userId": user_id,
            "userType": user_type,
            "event": event,
            "data": data
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload)
                if response.status_code not in (200, 202):
                    print(f"Event notification failed for {user_id}. Status: {response.status_code}. Response: {response.text}")
                else:
                    print(f"Event notification successfully triggered for {user_id}")
            except Exception as e:
                print(f"Error calling event notification API for {user_id}: {e}")

# Instantiate a global service object to be imported elsewhere
notification_service = NotificationService()