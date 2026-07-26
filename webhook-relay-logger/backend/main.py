"""
Webhook Relay & Logger API
FastAPI application for catching, inspecting, forwarding, and replaying webhooks.
"""
from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, Union
import os
import json
import uuid
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .services.webhook_service import WebhookService
from .services.relay_service import RelayService
from .services.storage_service import StorageService
from .services.auth_service import AuthService
from .models.schemas import (
    WebhookPayload, WebhookEndpoint, RelayRule, 
    WebhookLog, WebhookFilter, ReplayRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
webhook_service = WebhookService()
relay_service = RelayService()
storage_service = StorageService()
auth_service = AuthService()
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Webhook Relay & Logger API...")
    await webhook_service.initialize()
    await relay_service.initialize()
    await storage_service.initialize()
    yield
    logger.info("Shutting down Webhook Relay & Logger API...")
    await webhook_service.cleanup()
    await relay_service.cleanup()

app = FastAPI(
    title="Webhook Relay & Logger API",
    description="Catch, inspect, forward, and replay webhooks with advanced debugging capabilities",
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

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token."""
    user = await auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return user

# Optional auth for webhook endpoints
async def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """Optional authentication for webhook endpoints."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        return await auth_service.verify_token(token)
    return None

# Root endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Welcome to Webhook Relay & Logger API",
        "version": "1.0.0",
        "features": [
            "Webhook catching and inspection",
            "Real-time payload forwarding",
            "Advanced filtering and transformation",
            "Webhook replay functionality",
            "Web dashboard for debugging",
            "Analytics and monitoring"
        ],
        "dashboard": "/dashboard",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "webhook": await webhook_service.health_check(),
            "relay": await relay_service.health_check(),
            "storage": await storage_service.health_check()
        }
    }

# Webhook Catching Endpoints
@app.api_route("/webhook/{endpoint_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_webhook(
    endpoint_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: Optional[Dict[str, Any]] = Depends(optional_auth)
):
    """Universal webhook catcher endpoint."""
    try:
        # Capture all request data
        headers = dict(request.headers)
        method = request.method
        url = str(request.url)
        query_params = dict(request.query_params)
        
        # Get request body
        body = None
        content_type = headers.get("content-type", "")
        
        if method in ["POST", "PUT", "PATCH"]:
            try:
                if "application/json" in content_type:
                    body = await request.json()
                elif "application/x-www-form-urlencoded" in content_type:
                    form_data = await request.form()
                    body = dict(form_data)
                else:
                    body_bytes = await request.body()
                    body = body_bytes.decode() if body_bytes else None
            except Exception as e:
                logger.warning(f"Failed to parse body: {e}")
                body = str(await request.body())

        # Create webhook payload
        webhook_data = WebhookPayload(
            id=str(uuid.uuid4()),
            endpoint_id=endpoint_id,
            method=method,
            url=url,
            headers=headers,
            query_params=query_params,
            body=body,
            timestamp=datetime.utcnow(),
            user_id=user["id"] if user else None
        )

        # Store webhook
        await storage_service.store_webhook(webhook_data)

        # Process in background
        background_tasks.add_task(
            webhook_service.process_webhook,
            webhook_data
        )

        # Log the webhook
        logger.info(f"Webhook received: {method} {endpoint_id}")

        return {
            "status": "received",
            "webhook_id": webhook_data.id,
            "endpoint_id": endpoint_id,
            "timestamp": webhook_data.timestamp
        }

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Webhook processing failed", "detail": str(e)}
        )

# Webhook Management Endpoints
@app.post("/endpoints")
async def create_endpoint(
    endpoint: WebhookEndpoint,
    user = Depends(get_current_user)
):
    """Create a new webhook endpoint."""
    try:
        endpoint_id = await webhook_service.create_endpoint(
            user_id=user["id"],
            endpoint=endpoint
        )
        return {
            "endpoint_id": endpoint_id,
            "webhook_url": f"/webhook/{endpoint_id}",
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/endpoints")
async def list_endpoints(
    user = Depends(get_current_user)
) -> List[WebhookEndpoint]:
    """List all webhook endpoints for user."""
    try:
        endpoints = await webhook_service.list_endpoints(user["id"])
        return endpoints
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/endpoints/{endpoint_id}")
async def get_endpoint(
    endpoint_id: str,
    user = Depends(get_current_user)
) -> WebhookEndpoint:
    """Get specific webhook endpoint."""
    try:
        endpoint = await webhook_service.get_endpoint(user["id"], endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return endpoint
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/endpoints/{endpoint_id}")
async def update_endpoint(
    endpoint_id: str,
    endpoint: WebhookEndpoint,
    user = Depends(get_current_user)
):
    """Update webhook endpoint."""
    try:
        await webhook_service.update_endpoint(user["id"], endpoint_id, endpoint)
        return {"status": "updated", "endpoint_id": endpoint_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(
    endpoint_id: str,
    user = Depends(get_current_user)
):
    """Delete webhook endpoint."""
    try:
        await webhook_service.delete_endpoint(user["id"], endpoint_id)
        return {"status": "deleted", "endpoint_id": endpoint_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Webhook Logs and Inspection
@app.get("/webhooks")
async def list_webhooks(
    endpoint_id: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    method: Optional[str] = None,
    status: Optional[str] = None,
    user = Depends(get_current_user)
) -> List[WebhookLog]:
    """List webhook logs with filtering."""
    try:
        filters = WebhookFilter(
            endpoint_id=endpoint_id,
            method=method,
            status=status
        )
        webhooks = await storage_service.get_webhooks(
            user_id=user["id"],
            filters=filters,
            limit=limit,
            offset=offset
        )
        return webhooks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhooks/{webhook_id}")
async def get_webhook_detail(
    webhook_id: str,
    user = Depends(get_current_user)
) -> WebhookPayload:
    """Get detailed webhook information."""
    try:
        webhook = await storage_service.get_webhook(user["id"], webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Relay and Forwarding
@app.post("/relays")
async def create_relay_rule(
    relay: RelayRule,
    user = Depends(get_current_user)
):
    """Create webhook relay rule."""
    try:
        rule_id = await relay_service.create_rule(user["id"], relay)
        return {"rule_id": rule_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/relays")
async def list_relay_rules(
    user = Depends(get_current_user)
) -> List[RelayRule]:
    """List all relay rules."""
    try:
        rules = await relay_service.list_rules(user["id"])
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/relays/{rule_id}")
async def update_relay_rule(
    rule_id: str,
    relay: RelayRule,
    user = Depends(get_current_user)
):
    """Update relay rule."""
    try:
        await relay_service.update_rule(user["id"], rule_id, relay)
        return {"status": "updated", "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/relays/{rule_id}")
async def delete_relay_rule(
    rule_id: str,
    user = Depends(get_current_user)
):
    """Delete relay rule."""
    try:
        await relay_service.delete_rule(user["id"], rule_id)
        return {"status": "deleted", "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Replay Functionality
@app.post("/webhooks/{webhook_id}/replay")
async def replay_webhook(
    webhook_id: str,
    replay_request: ReplayRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Replay a webhook to specified endpoints."""
    try:
        webhook = await storage_service.get_webhook(user["id"], webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        # Start replay in background
        background_tasks.add_task(
            relay_service.replay_webhook,
            webhook,
            replay_request.target_urls
        )

        return {
            "status": "replay_started",
            "webhook_id": webhook_id,
            "targets": len(replay_request.target_urls)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Analytics and Monitoring
@app.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=90),
    user = Depends(get_current_user)
):
    """Get webhook analytics summary."""
    try:
        analytics = await storage_service.get_analytics(user["id"], days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/endpoints/{endpoint_id}")
async def get_endpoint_analytics(
    endpoint_id: str,
    days: int = Query(7, ge=1, le=90),
    user = Depends(get_current_user)
):
    """Get analytics for specific endpoint."""
    try:
        analytics = await storage_service.get_endpoint_analytics(
            user["id"], endpoint_id, days
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Web Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Web dashboard for webhook inspection."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webhook Relay & Logger Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .webhook { border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; background: #f8f9fa; }
            .method { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }
            .get { background: #28a745; }
            .post { background: #007bff; }
            .put { background: #ffc107; color: #000; }
            .delete { background: #dc3545; }
            .timestamp { color: #666; font-size: 14px; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔗 Webhook Relay & Logger</h1>
                <p>Real-time webhook debugging and relay dashboard</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📥 Recent Webhooks</h3>
                    <div id="webhooks">
                        <p>Loading webhooks...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📊 Statistics</h3>
                    <div id="stats">
                        <p>Loading statistics...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎯 Active Endpoints</h3>
                    <div id="endpoints">
                        <p>Loading endpoints...</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Simple dashboard functionality
            async function loadDashboard() {
                try {
                    // This would connect to the API endpoints
                    document.getElementById('webhooks').innerHTML = `
                        <div class="webhook">
                            <span class="method post">POST</span>
                            <strong>/webhook/demo</strong>
                            <div class="timestamp">2 minutes ago</div>
                        </div>
                    `;
                    
                    document.getElementById('stats').innerHTML = `
                        <p><strong>Today:</strong> 42 webhooks</p>
                        <p><strong>This week:</strong> 234 webhooks</p>
                        <p><strong>Success rate:</strong> 98.5%</p>
                    `;
                    
                    document.getElementById('endpoints').innerHTML = `
                        <p>📍 <code>/webhook/api-integration</code></p>
                        <p>📍 <code>/webhook/payment-notifications</code></p>
                        <p>📍 <code>/webhook/user-events</code></p>
                    `;
                } catch (error) {
                    console.error('Dashboard load failed:', error);
                }
            }
            
            loadDashboard();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboard, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Testing and Utilities
@app.post("/test/webhook")
async def test_webhook_endpoint():
    """Test endpoint for webhook functionality."""
    return {
        "message": "Test webhook endpoint working",
        "timestamp": datetime.utcnow(),
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
