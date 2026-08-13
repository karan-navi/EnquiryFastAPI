from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

# --- Sub-schemas for Relationships ---

class EnquiryHistorySchema(BaseModel):
    id: str
    enquiryId: str
    notes: Optional[str] = None
    status: str
    updateTimestamp: datetime
    updatedByUserId: str

    # This allows Pydantic to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True) 

# --- Requests (Incoming Data) ---

class EnquiryRequest(BaseModel):
    userId: str
    serviceId: str
    title: str = Field(..., max_length=100)
    description: str

class CommentRequest(BaseModel):
    comment: str

class StatusUpdateRequest(BaseModel):
    newStatus: str
    notes: Optional[str] = None
    salesPersonName: Optional[str] = None
    salesRepId: Optional[str] = None

# --- Responses (Outgoing Data) ---

class EnquiryResponse(BaseModel):
    id: str
    title: Optional[str] = None
    customerId: Optional[str] = None
    description: Optional[str] = None
    currentStatus: Optional[str] = None
    submissionDate: Optional[datetime] = None
    timeline: List[EnquiryHistorySchema] = []

    model_config = ConfigDict(from_attributes=True)

class PagedResult(BaseModel):
    items: List[Any]
    totalCount: int
    page: int
    pageSize: int

class RequestFilter(BaseModel):
    page: int = 1
    pageSize: int = 10
    searchTerms: Optional[str] = None
    sortBy: Optional[str] = None
    sortDescending: bool = False
    isActive: Optional[bool] = None