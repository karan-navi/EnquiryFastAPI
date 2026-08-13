from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.config import settings
from app.api import user, admin
from app.services.reminder import send_assignment_reminders
import asyncio

# Initialize Background Scheduler for Cron jobs (replaces Spring @Scheduled)
scheduler = BackgroundScheduler()

def run_reminder_job():
    asyncio.run(send_assignment_reminders())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Register and start scheduler (Cron: twice daily at 00:00 and 12:00)
    scheduler.add_job(run_reminder_job, 'cron', hour='0,12', minute=0)
    scheduler.start()
    yield
    # Shutdown: Stop scheduler
    scheduler.shutdown()

app = FastAPI(title="Enquiry Management and Tracking System", lifespan=lifespan)

# Global Exception Handler (replaces GlobalExceptionHandler.java)[cite: 26]
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": 500,
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Include Routers
app.include_router(user.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Enquiry Management System FastAPI is running!"}