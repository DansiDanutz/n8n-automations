"""
AI Email Assistant API
FastAPI application for intelligent email management and automation.
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager

from .services.email_service import EmailService
from .services.ai_service import AIService
from .services.auth_service import AuthService
from .database.db import get_db_session
from .models.schemas import (
    EmailSummary, EmailReply, EmailCategory, 
    PriorityScore, SpamDetection, WebhookPayload
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
email_service = EmailService()
ai_service = AIService()
auth_service = AuthService()
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Email Assistant API...")
    await email_service.initialize()
    await ai_service.initialize()
    yield
    logger.info("Shutting down AI Email Assistant API...")
    await email_service.cleanup()

app = FastAPI(
    title="AI Email Assistant API",
    description="Intelligent email management with AI-powered summarization, categorization, and automation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token."""
    user = await auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return user

# Root endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Welcome to AI Email Assistant API",
        "version": "1.0.0",
        "features": [
            "Email summarization",
            "AI-powered reply generation", 
            "Smart categorization",
            "Priority scoring",
            "Spam detection",
            "Webhook integration"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "email": await email_service.health_check(),
            "ai": await ai_service.health_check()
        }
    }

# Email Management Endpoints
@app.post("/emails/connect")
async def connect_email_account(
    provider: str,
    credentials: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Connect email account (Gmail/Outlook)."""
    try:
        account_id = await email_service.connect_account(
            user_id=user["id"],
            provider=provider,
            credentials=credentials
        )
        return {"account_id": account_id, "status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/emails/inbox")
async def get_inbox_emails(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Retrieve inbox emails with optional filtering."""
    try:
        emails = await email_service.get_inbox(
            user_id=user["id"],
            limit=limit,
            offset=offset,
            category=category
        )
        return {"emails": emails, "total": len(emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/summarize")
async def summarize_email(
    email_id: str,
    user = Depends(get_current_user)
) -> EmailSummary:
    """Generate AI summary of email."""
    try:
        email = await email_service.get_email(user["id"], email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        summary = await ai_service.summarize_email(email)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/reply")
async def generate_reply(
    email_id: str,
    context: Optional[str] = None,
    tone: str = "professional",
    user = Depends(get_current_user)
) -> EmailReply:
    """Generate AI-powered email reply."""
    try:
        email = await email_service.get_email(user["id"], email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        reply = await ai_service.generate_reply(email, context, tone)
        return reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/categorize")
async def categorize_email(
    email_id: str,
    user = Depends(get_current_user)
) -> EmailCategory:
    """Categorize email using AI."""
    try:
        email = await email_service.get_email(user["id"], email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        category = await ai_service.categorize_email(email)
        await email_service.update_email_category(email_id, category.category)
        return category
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/priority")
async def score_priority(
    email_id: str,
    user = Depends(get_current_user)
) -> PriorityScore:
    """Calculate email priority score."""
    try:
        email = await email_service.get_email(user["id"], email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        priority = await ai_service.score_priority(email)
        await email_service.update_email_priority(email_id, priority.score)
        return priority
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/spam-check")
async def detect_spam(
    email_id: str,
    user = Depends(get_current_user)
) -> SpamDetection:
    """Detect if email is spam."""
    try:
        email = await email_service.get_email(user["id"], email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        spam_result = await ai_service.detect_spam(email)
        if spam_result.is_spam:
            await email_service.mark_as_spam(email_id)
        return spam_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk Operations
@app.post("/emails/bulk/process")
async def bulk_process_emails(
    background_tasks: BackgroundTasks,
    limit: int = 100,
    user = Depends(get_current_user)
):
    """Process multiple emails in background."""
    background_tasks.add_task(
        email_service.bulk_process_emails,
        user["id"],
        limit
    )
    return {"status": "processing", "message": f"Processing up to {limit} emails"}

# Analytics & Insights
@app.get("/analytics/summary")
async def get_email_analytics(
    days: int = 7,
    user = Depends(get_current_user)
):
    """Get email analytics summary."""
    try:
        analytics = await email_service.get_analytics(user["id"], days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Webhook Endpoints for n8n Integration
@app.post("/webhooks/email-received")
async def webhook_email_received(payload: WebhookPayload):
    """Webhook endpoint for new email notifications."""
    try:
        result = await email_service.process_webhook_email(payload)
        return {"status": "processed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/bulk-process")
async def webhook_bulk_process(
    background_tasks: BackgroundTasks,
    payload: WebhookPayload
):
    """Webhook endpoint for bulk processing trigger."""
    user_id = payload.data.get("user_id")
    limit = payload.data.get("limit", 50)
    
    background_tasks.add_task(
        email_service.bulk_process_emails,
        user_id,
        limit
    )
    return {"status": "triggered", "message": "Bulk processing started"}

# Configuration Endpoints
@app.get("/config/categories")
async def get_email_categories():
    """Get available email categories."""
    return {
        "categories": [
            "work", "personal", "promotions", "social", 
            "updates", "forums", "newsletters", "spam"
        ]
    }

@app.get("/config/priorities")
async def get_priority_levels():
    """Get priority scoring levels."""
    return {
        "levels": {
            "urgent": {"min": 8, "max": 10, "color": "red"},
            "high": {"min": 6, "max": 7, "color": "orange"}, 
            "medium": {"min": 4, "max": 5, "color": "yellow"},
            "low": {"min": 1, "max": 3, "color": "green"}
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)