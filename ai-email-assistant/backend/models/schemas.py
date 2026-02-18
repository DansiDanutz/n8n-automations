"""
Pydantic models for AI Email Assistant API.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmailProvider(str, Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"

class EmailCategory(BaseModel):
    """Email category model."""
    category: str = Field(..., description="Email category")
    confidence: float = Field(..., description="Category confidence score", ge=0, le=1)
    subcategory: Optional[str] = Field(None, description="Subcategory if applicable")

class PriorityLevel(str, Enum):
    """Priority levels."""
    URGENT = "urgent"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class PriorityScore(BaseModel):
    """Email priority score model."""
    score: int = Field(..., description="Priority score 1-10", ge=1, le=10)
    level: PriorityLevel = Field(..., description="Priority level")
    factors: List[str] = Field(default_factory=list, description="Factors affecting priority")
    
class SpamDetection(BaseModel):
    """Spam detection result."""
    is_spam: bool = Field(..., description="Whether email is spam")
    confidence: float = Field(..., description="Spam confidence score", ge=0, le=1)
    reasons: List[str] = Field(default_factory=list, description="Spam indicators")

class EmailSummary(BaseModel):
    """Email summary model."""
    summary: str = Field(..., description="Brief email summary")
    key_points: List[str] = Field(default_factory=list, description="Key points")
    sentiment: str = Field(..., description="Email sentiment")
    urgency: str = Field(..., description="Urgency level")
    action_required: bool = Field(..., description="Whether action is required")

class EmailReply(BaseModel):
    """Generated email reply model."""
    subject: str = Field(..., description="Reply subject")
    body: str = Field(..., description="Reply body")
    tone: str = Field(..., description="Reply tone")
    suggestions: List[str] = Field(default_factory=list, description="Alternative responses")

class Email(BaseModel):
    """Email model."""
    id: str = Field(..., description="Email ID")
    subject: str = Field(..., description="Email subject")
    sender: EmailStr = Field(..., description="Sender email")
    recipient: EmailStr = Field(..., description="Recipient email")
    body: str = Field(..., description="Email body")
    html_body: Optional[str] = Field(None, description="HTML email body")
    received_at: datetime = Field(..., description="Email received timestamp")
    attachments: List[str] = Field(default_factory=list, description="Attachment filenames")
    is_read: bool = Field(default=False, description="Whether email is read")
    category: Optional[str] = Field(None, description="Email category")
    priority_score: Optional[int] = Field(None, description="Priority score")
    is_spam: bool = Field(default=False, description="Whether email is spam")

class EmailConnection(BaseModel):
    """Email account connection model."""
    provider: EmailProvider = Field(..., description="Email provider")
    email_address: EmailStr = Field(..., description="Email address")
    credentials: Dict[str, Any] = Field(..., description="Authentication credentials")
    
class WebhookPayload(BaseModel):
    """Webhook payload model."""
    event: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")

class BulkProcessRequest(BaseModel):
    """Bulk process request model."""
    user_id: str = Field(..., description="User ID")
    limit: int = Field(default=50, description="Number of emails to process", ge=1, le=500)
    filters: Optional[Dict[str, Any]] = Field(None, description="Email filters")

class AnalyticsResponse(BaseModel):
    """Email analytics response model."""
    total_emails: int = Field(..., description="Total emails")
    unread_count: int = Field(..., description="Unread emails")
    spam_count: int = Field(..., description="Spam emails") 
    category_breakdown: Dict[str, int] = Field(..., description="Emails by category")
    priority_breakdown: Dict[str, int] = Field(..., description="Emails by priority")
    daily_volume: List[Dict[str, Any]] = Field(..., description="Daily email volume")
    top_senders: List[Dict[str, Any]] = Field(..., description="Top email senders")

class UserPreferences(BaseModel):
    """User preferences model."""
    auto_categorize: bool = Field(default=True, description="Auto-categorize emails")
    auto_priority: bool = Field(default=True, description="Auto-assign priority")
    spam_filter: bool = Field(default=True, description="Enable spam filtering")
    summary_length: str = Field(default="medium", description="Summary length preference")
    reply_tone: str = Field(default="professional", description="Default reply tone")

class AuthToken(BaseModel):
    """Authentication token model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

class UserRegistration(BaseModel):
    """User registration model."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=8)
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")

class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")

class APIError(BaseModel):
    """API error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")