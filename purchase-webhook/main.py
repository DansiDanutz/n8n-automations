#!/usr/bin/env python3
"""
Stripe Webhook → GitHub Auto-Access Automation
Handles Stripe checkout.session.completed events and automatically grants GitHub repo access.
"""

import asyncio
import hashlib
import hmac
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import stripe
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Product → GitHub repo mapping
PRODUCT_REPO_MAPPING = {
    "ai-customer-support-bot": "DansiDanutz/ai-customer-support-bot",
    "invoice-generator-api": "DansiDanutz/invoice-generator-api", 
    "social-media-auto-poster": "DansiDanutz/social-media-auto-poster",
    "ai-email-assistant": "DansiDanutz/ai-email-assistant",
    "webhook-relay-logger": "DansiDanutz/webhook-relay-logger",
    "ai-seo-content-generator": "DansiDanutz/ai-seo-content-generator",
    "appointment-booking-system": "DansiDanutz/appointment-booking-system",
    "ai-data-scraper": "DansiDanutz/ai-data-scraper",
    "smart-lead-nurture": "DansiDanutz/smart-lead-nurture",
}

# Environment variables
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "DansiDanutz")


def required_secret(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be configured with at least {minimum_length} characters")
    return value


STRIPE_WEBHOOK_SECRET = required_secret("STRIPE_WEBHOOK_SECRET", 16)
GITHUB_TOKEN = required_secret("GITHUB_TOKEN", 20)
MANAGEMENT_API_KEY = required_secret("MANAGEMENT_API_KEY", 32)

# Configure Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# In-memory storage for purchases (replace with database in production)
purchases_store: List[Dict] = []
processed_event_ids: set[str] = set()
inflight_event_ids: set[str] = set()
event_lock = asyncio.Lock()

class PurchaseRecord(BaseModel):
    """Purchase record model"""
    id: str
    email: str
    product_id: str
    product_name: Optional[str] = None
    github_repo: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    payment_status: str
    github_access_granted: bool = False
    github_invitation_url: Optional[str] = None
    created_at: datetime
    stripe_session_id: str
    error_message: Optional[str] = None

class WebhookResponse(BaseModel):
    """Webhook response model"""
    status: str
    message: str
    purchase_id: Optional[str] = None
    github_repo: Optional[str] = None
    github_access_granted: bool = False

async def verify_stripe_signature(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature"""
    try:
        stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return True
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return False
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return False

async def add_github_collaborator(repo: str, email: str) -> Dict:
    """Add user as collaborator to GitHub repository"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "purchase-webhook/1.0"
    }
    
    # First, try to find user by email
    async with httpx.AsyncClient() as client:
        # Search for user by email
        search_url = f"https://api.github.com/search/users?q={email}+in:email"
        try:
            search_response = await client.get(search_url, headers=headers)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get("total_count", 0) > 0:
                    username = search_data["items"][0]["login"]
                    logger.info(f"Found GitHub user {username} for email {email}")
                else:
                    logger.warning(f"No GitHub user found for email {email}")
                    return {"success": False, "error": "GitHub user not found for this email"}
            else:
                logger.error(f"GitHub user search failed: {search_response.status_code}")
                return {"success": False, "error": "Failed to search for GitHub user"}
        except Exception as e:
            logger.error(f"Error searching for GitHub user: {e}")
            return {"success": False, "error": f"Error searching for user: {str(e)}"}
    
        # Add user as collaborator with read access
        collab_url = f"https://api.github.com/repos/{repo}/collaborators/{username}"
        collab_data = {"permission": "pull"}  # read access only
        
        try:
            collab_response = await client.put(collab_url, headers=headers, json=collab_data)
            if collab_response.status_code in [201, 204]:
                logger.info(f"Successfully invited {username} to {repo}")
                invitation_data = collab_response.json() if collab_response.status_code == 201 else {}
                return {
                    "success": True, 
                    "username": username,
                    "invitation_url": invitation_data.get("html_url"),
                    "message": f"Invitation sent to {username}"
                }
            elif collab_response.status_code == 422:
                logger.info(f"User {username} is already a collaborator on {repo}")
                return {
                    "success": True,
                    "username": username, 
                    "message": f"{username} is already a collaborator"
                }
            else:
                error_data = collab_response.json()
                logger.error(f"Failed to add collaborator: {collab_response.status_code} - {error_data}")
                return {"success": False, "error": f"GitHub API error: {error_data.get('message', 'Unknown error')}"}
        except Exception as e:
            logger.error(f"Error adding GitHub collaborator: {e}")
            return {"success": False, "error": f"Error adding collaborator: {str(e)}"}

async def process_successful_payment(session_data: Dict) -> PurchaseRecord:
    """Process successful Stripe payment"""
    session_id = session_data["id"]
    customer_email = session_data["customer_details"]["email"]
    amount_total = session_data["amount_total"]
    currency = session_data["currency"]
    
    # Extract product information from metadata or line items
    product_id = None
    product_name = None
    
    # Try to get product info from metadata first
    if "metadata" in session_data and "product_id" in session_data["metadata"]:
        product_id = session_data["metadata"]["product_id"]
        product_name = session_data["metadata"].get("product_name")
    
    # If not in metadata, try to extract from line items
    if not product_id and "line_items" in session_data:
        for item in session_data["line_items"]["data"]:
            if item.get("price", {}).get("metadata", {}).get("product_id"):
                product_id = item["price"]["metadata"]["product_id"]
                product_name = item.get("description") or item.get("price", {}).get("product", {}).get("name")
                break
    
    # Get GitHub repo for the product
    github_repo = PRODUCT_REPO_MAPPING.get(product_id) if product_id else None
    
    # Create purchase record
    purchase = PurchaseRecord(
        id=f"purchase_{session_id}_{int(datetime.now().timestamp())}",
        email=customer_email,
        product_id=product_id or "unknown",
        product_name=product_name,
        github_repo=github_repo,
        amount=amount_total,
        currency=currency,
        payment_status="completed",
        stripe_session_id=session_id,
        created_at=datetime.now()
    )
    
    # Add GitHub access if we have a repo mapping
    if github_repo:
        logger.info(f"Granting access to {github_repo} for {customer_email}")
        github_result = await add_github_collaborator(github_repo, customer_email)
        
        if github_result["success"]:
            purchase.github_access_granted = True
            purchase.github_invitation_url = github_result.get("invitation_url")
            logger.info(f"GitHub access granted successfully for {customer_email}")
        else:
            purchase.error_message = github_result["error"]
            logger.error(f"Failed to grant GitHub access: {github_result['error']}")
    else:
        logger.warning(f"No GitHub repo mapping found for product_id: {product_id}")
        purchase.error_message = f"No repository mapping found for product: {product_id}"
    
    # Store purchase record
    purchases_store.append(purchase.dict())
    
    return purchase

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 Purchase webhook service starting up...")
    logger.info(f"GitHub token configured: {'✅' if GITHUB_TOKEN else '❌'}")
    logger.info(f"Stripe webhook secret configured: {'✅' if STRIPE_WEBHOOK_SECRET else '❌'}")
    logger.info(f"Product mappings loaded: {len(PRODUCT_REPO_MAPPING)} products")
    yield
    logger.info("🛑 Purchase webhook service shutting down...")

# FastAPI app
app = FastAPI(
    title="Purchase Webhook Service",
    description="Stripe webhook handler for automatic GitHub repository access",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def authenticate_purchase_records(request: Request, call_next):
    if request.url.path.startswith("/purchases"):
        supplied_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(supplied_key.encode(), MANAGEMENT_API_KEY.encode()):
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
    return await call_next(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "purchase-webhook",
        "version": "1.0.0",
        "github_configured": bool(GITHUB_TOKEN),
        "stripe_webhook_configured": bool(STRIPE_WEBHOOK_SECRET),
        "total_purchases": len(purchases_store)
    }

@app.post("/webhook/stripe", response_model=WebhookResponse)
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    # Verify signature
    if not await verify_stripe_signature(payload, sig_header):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_id = event.get("id")
    event_type = event.get("type")
    if not isinstance(event_id, str) or not event_id or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="Invalid Stripe event")
    logger.info(f"Received Stripe event: {event_type}")
    
    if event_type == "checkout.session.completed":
        async with event_lock:
            if event_id in processed_event_ids or event_id in inflight_event_ids:
                return WebhookResponse(status="ignored", message="Stripe event already processed")
            inflight_event_ids.add(event_id)

        completed = False
        try:
            session_data = event["data"]["object"]

            # Only process successful payments
            if session_data.get("payment_status") == "paid":
                purchase = await process_successful_payment(session_data)
                completed = True
                return WebhookResponse(
                    status="success",
                    message="Purchase processed and GitHub access granted",
                    purchase_id=purchase.id,
                    github_repo=purchase.github_repo,
                    github_access_granted=purchase.github_access_granted
                )
                
            logger.info("Payment not completed, skipping GitHub access")
            completed = True
            return WebhookResponse(status="ignored", message="Payment not completed")
        except (KeyError, TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid checkout session")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Error processing payment")
            raise HTTPException(status_code=500, detail="Payment processing failed")
        finally:
            async with event_lock:
                inflight_event_ids.discard(event_id)
                if completed:
                    processed_event_ids.add(event_id)
    
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return WebhookResponse(
            status="ignored", 
            message=f"Event type {event_type} not handled"
        )

@app.get("/purchases")
async def get_purchases(limit: int = 100, email: Optional[str] = None):
    """Get list of purchases"""
    filtered_purchases = purchases_store
    
    if email:
        filtered_purchases = [p for p in purchases_store if p["email"].lower() == email.lower()]
    
    return {
        "purchases": filtered_purchases[-limit:],  # Get latest purchases
        "total": len(filtered_purchases),
        "filtered_by_email": email is not None
    }

@app.get("/purchases/{purchase_id}")
async def get_purchase(purchase_id: str):
    """Get specific purchase details"""
    purchase = next((p for p in purchases_store if p["id"] == purchase_id), None)
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    return purchase

@app.get("/products/mappings")
async def get_product_mappings():
    """Get product to GitHub repository mappings"""
    return {
        "mappings": PRODUCT_REPO_MAPPING,
        "total_products": len(PRODUCT_REPO_MAPPING)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
