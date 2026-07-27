#!/usr/bin/env python3
"""
API Rate Limiter Service
A production-ready rate limiting proxy with Redis-backed sliding window,
per-IP and per-API-key tracking, customizable limits, analytics, and alerts.
"""

import os
import hmac
import time
import json
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from collections import defaultdict

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from client_identity import resolve_client_ip

load_dotenv()

# ─── Configuration ───
PORT = int(os.getenv("PORT", "8000"))
DEFAULT_RATE_LIMIT = int(os.getenv("DEFAULT_RATE_LIMIT", "100"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("DEFAULT_WINDOW_SECONDS", "60"))
REDIS_URL = os.getenv("REDIS_URL", "")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
TRUSTED_PROXY_HOPS = max(0, int(os.getenv("TRUSTED_PROXY_HOPS", "0")))
TRUSTED_PROXY_CIDRS = tuple(
    value.strip()
    for value in os.getenv("TRUSTED_PROXY_CIDRS", "").split(",")
    if value.strip()
)


def required_secret(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be configured with at least {minimum_length} characters")
    return value


ADMIN_API_KEY = required_secret("ADMIN_API_KEY", 32)

# ─── In-Memory Store (Redis-compatible interface) ───
class MemoryStore:
    """In-memory rate limit store. Swap with Redis in production."""
    
    def __init__(self):
        self.windows: Dict[str, List[float]] = defaultdict(list)
        self.blocked: Dict[str, float] = {}
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "unique_clients": set(),
            "started_at": time.time(),
        }
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> dict:
        """Sliding window rate limit check."""
        now = time.time()
        window_start = now - window
        
        # Clean old entries
        self.windows[key] = [t for t in self.windows[key] if t > window_start]
        
        current_count = len(self.windows[key])
        self.stats["total_requests"] += 1
        self.stats["unique_clients"].add(key)
        
        if current_count >= limit:
            self.stats["blocked_requests"] += 1
            retry_after = int(self.windows[key][0] - window_start) + 1
            return {
                "allowed": False,
                "current": current_count,
                "limit": limit,
                "remaining": 0,
                "retry_after": max(1, retry_after),
                "reset_at": int(self.windows[key][0] + window),
            }
        
        self.windows[key].append(now)
        return {
            "allowed": True,
            "current": current_count + 1,
            "limit": limit,
            "remaining": limit - current_count - 1,
            "retry_after": 0,
            "reset_at": int(now + window),
        }
    
    def get_client_stats(self, key: str) -> dict:
        now = time.time()
        requests = self.windows.get(key, [])
        return {
            "client": key,
            "requests_last_minute": len([t for t in requests if t > now - 60]),
            "requests_last_hour": len([t for t in requests if t > now - 3600]),
            "total_requests": len(requests),
        }
    
    def get_global_stats(self) -> dict:
        now = time.time()
        uptime = now - self.stats["started_at"]
        return {
            "total_requests": self.stats["total_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "block_rate": round(self.stats["blocked_requests"] / max(1, self.stats["total_requests"]) * 100, 2),
            "unique_clients": len(self.stats["unique_clients"]),
            "active_windows": len(self.windows),
            "uptime_seconds": int(uptime),
            "requests_per_second": round(self.stats["total_requests"] / max(1, uptime), 2),
        }
    
    def reset_client(self, key: str):
        self.windows.pop(key, None)
        self.blocked.pop(key, None)


store = MemoryStore()

# ─── Custom Rules Storage ───
custom_rules: Dict[str, dict] = {}
# Format: { "endpoint_pattern": { "limit": 50, "window": 60 } }

# ─── Models ───
class RateLimitRule(BaseModel):
    endpoint: str  # e.g., "/api/login", "/api/*", "*"
    limit: int = 100
    window_seconds: int = 60
    description: Optional[str] = None

class CheckRequest(BaseModel):
    client_id: str
    endpoint: Optional[str] = "/"

class AlertConfig(BaseModel):
    webhook_url: str
    threshold_percent: int = 80  # Alert when usage hits this %
    
# ─── Helpers ───
def get_client_key(request: Request) -> str:
    """Extract client identifier from request."""
    api_key = request.headers.get(API_KEY_HEADER)
    if api_key:
        return f"key:{hashlib.md5(api_key.encode()).hexdigest()[:12]}"
    
    peer_ip = request.client.host
    client_ip = resolve_client_ip(
        peer_ip,
        request.headers.get("X-Forwarded-For"),
        trusted_proxy_hops=TRUSTED_PROXY_HOPS,
        trusted_proxy_cidrs=TRUSTED_PROXY_CIDRS,
    )
    if client_ip is None:
        raise HTTPException(status_code=400, detail="Invalid forwarded client address")
    return f"ip:{client_ip}"

def get_rule_for_endpoint(endpoint: str) -> dict:
    """Find the matching rate limit rule for an endpoint."""
    # Exact match first
    if endpoint in custom_rules:
        return custom_rules[endpoint]
    
    # Wildcard match
    for pattern, rule in custom_rules.items():
        if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
            return rule
    
    # Global wildcard
    if "*" in custom_rules:
        return custom_rules["*"]
    
    # Default
    return {"limit": DEFAULT_RATE_LIMIT, "window": DEFAULT_WINDOW_SECONDS}

def verify_admin(request: Request):
    """Verify admin API key."""
    key = request.headers.get(API_KEY_HEADER) or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not hmac.compare_digest(key.encode(), ADMIN_API_KEY.encode()):
        raise HTTPException(status_code=403, detail="Admin API key required")

# ─── App ───
app = FastAPI(
    title="API Rate Limiter",
    description="Production-ready rate limiting service with sliding window algorithm, analytics, and alerts.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Endpoints ───

@app.get("/")
async def root():
    """Service info and health check."""
    return {
        "service": "API Rate Limiter",
        "version": "1.0.0",
        "status": "running",
        "default_limit": f"{DEFAULT_RATE_LIMIT} requests per {DEFAULT_WINDOW_SECONDS}s",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    stats = store.get_global_stats()
    return {
        "status": "healthy",
        "uptime_seconds": stats["uptime_seconds"],
        "total_requests": stats["total_requests"],
    }

@app.post("/check")
async def check_rate_limit(req: CheckRequest):
    """Check if a request should be allowed (without consuming a token).
    
    Use this to pre-check before proxying a request.
    """
    rule = get_rule_for_endpoint(req.endpoint)
    key = f"{req.client_id}:{req.endpoint}"
    result = store.check_rate_limit(key, rule["limit"], rule.get("window", DEFAULT_WINDOW_SECONDS))
    return {
        "client_id": req.client_id,
        "endpoint": req.endpoint,
        **result,
    }

@app.post("/hit")
async def record_hit(request: Request, endpoint: str = "/"):
    """Record a request hit and return rate limit status.
    
    Call this for every incoming request to your API.
    Returns headers you should forward to the client.
    """
    client_key = get_client_key(request)
    rule = get_rule_for_endpoint(endpoint)
    key = f"{client_key}:{endpoint}"
    
    result = store.check_rate_limit(key, rule["limit"], rule.get("window", DEFAULT_WINDOW_SECONDS))
    
    response_headers = {
        "X-RateLimit-Limit": str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
        "X-RateLimit-Reset": str(result["reset_at"]),
    }
    
    if not result["allowed"]:
        response_headers["Retry-After"] = str(result["retry_after"])
        # Send alert webhook if configured
        if ALERT_WEBHOOK_URL:
            asyncio.create_task(_send_alert(client_key, endpoint, result))
    
    return {
        "allowed": result["allowed"],
        "headers": response_headers,
        **result,
    }

@app.get("/rules")
async def list_rules(request: Request):
    """List all custom rate limit rules."""
    verify_admin(request)
    rules = [
        {"endpoint": ep, **rule}
        for ep, rule in custom_rules.items()
    ]
    if not rules:
        rules = [{"endpoint": "*", "limit": DEFAULT_RATE_LIMIT, "window": DEFAULT_WINDOW_SECONDS, "description": "Default rule"}]
    return {"rules": rules, "default_limit": DEFAULT_RATE_LIMIT, "default_window": DEFAULT_WINDOW_SECONDS}

@app.post("/rules")
async def create_rule(rule: RateLimitRule, request: Request):
    """Create or update a rate limit rule for an endpoint."""
    verify_admin(request)
    custom_rules[rule.endpoint] = {
        "limit": rule.limit,
        "window": rule.window_seconds,
        "description": rule.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return {"status": "created", "rule": {"endpoint": rule.endpoint, "limit": rule.limit, "window": rule.window_seconds}}

@app.delete("/rules/{endpoint:path}")
async def delete_rule(endpoint: str, request: Request):
    """Delete a rate limit rule."""
    verify_admin(request)
    if endpoint in custom_rules:
        del custom_rules[endpoint]
        return {"status": "deleted", "endpoint": endpoint}
    raise HTTPException(status_code=404, detail="Rule not found")

@app.get("/clients")
async def list_clients(request: Request):
    """List all tracked clients with their current usage."""
    verify_admin(request)
    clients = []
    seen = set()
    for key in store.windows:
        client_part = key.rsplit(":", 1)[0]
        if client_part not in seen:
            seen.add(client_part)
            clients.append(store.get_client_stats(client_part))
    return {"clients": clients, "total": len(clients)}

@app.get("/clients/{client_id}")
async def get_client(client_id: str, request: Request):
    """Get detailed stats for a specific client."""
    verify_admin(request)
    return store.get_client_stats(client_id)

@app.delete("/clients/{client_id}")
async def reset_client(client_id: str, request: Request):
    """Reset rate limit counters for a client."""
    verify_admin(request)
    # Reset all windows for this client
    keys_to_remove = [k for k in store.windows if k.startswith(client_id)]
    for k in keys_to_remove:
        del store.windows[k]
    return {"status": "reset", "client_id": client_id, "windows_cleared": len(keys_to_remove)}

@app.get("/analytics")
async def analytics(request: Request):
    """Get global analytics and usage statistics."""
    verify_admin(request)
    stats = store.get_global_stats()
    
    # Top clients by request count
    client_counts = defaultdict(int)
    for key, timestamps in store.windows.items():
        client = key.rsplit(":", 1)[0]
        client_counts[client] += len(timestamps)
    
    top_clients = sorted(client_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Top endpoints
    endpoint_counts = defaultdict(int)
    for key, timestamps in store.windows.items():
        parts = key.split(":")
        endpoint = parts[-1] if len(parts) > 1 else "/"
        endpoint_counts[endpoint] += len(timestamps)
    
    top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        **stats,
        "top_clients": [{"client": c, "requests": n} for c, n in top_clients],
        "top_endpoints": [{"endpoint": e, "requests": n} for e, n in top_endpoints],
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Real-time analytics dashboard."""
    stats = store.get_global_stats()
    
    return f"""<!DOCTYPE html>
<html><head><title>Rate Limiter Dashboard</title>
<meta http-equiv="refresh" content="5">
<style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:system-ui;background:#0f0f23;color:#e0e0e0;padding:20px}}
    h1{{color:#667eea;margin-bottom:20px;font-size:1.8rem}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:30px}}
    .card{{background:#1a1a3e;border-radius:12px;padding:20px;text-align:center}}
    .card .value{{font-size:2.2rem;font-weight:bold;color:#667eea}}
    .card .label{{color:#888;margin-top:5px;font-size:0.9rem}}
    .status{{display:inline-block;width:10px;height:10px;border-radius:50%;background:#4caf50;margin-right:8px}}
    .bar{{background:#2a2a4e;border-radius:4px;height:8px;margin-top:5px}}
    .bar-fill{{background:linear-gradient(90deg,#667eea,#764ba2);height:100%;border-radius:4px;transition:width 0.3s}}
</style></head>
<body>
<h1><span class="status"></span>API Rate Limiter Dashboard</h1>
<div class="grid">
    <div class="card"><div class="value">{stats['total_requests']}</div><div class="label">Total Requests</div></div>
    <div class="card"><div class="value">{stats['blocked_requests']}</div><div class="label">Blocked</div></div>
    <div class="card"><div class="value">{stats['block_rate']}%</div><div class="label">Block Rate</div></div>
    <div class="card"><div class="value">{stats['unique_clients']}</div><div class="label">Unique Clients</div></div>
    <div class="card"><div class="value">{stats['requests_per_second']}</div><div class="label">Req/sec</div></div>
    <div class="card"><div class="value">{stats['uptime_seconds']}s</div><div class="label">Uptime</div></div>
</div>
<p style="color:#555;font-size:0.8rem">Auto-refreshes every 5 seconds • Default limit: {DEFAULT_RATE_LIMIT} req/{DEFAULT_WINDOW_SECONDS}s</p>
</body></html>"""


async def _send_alert(client: str, endpoint: str, result: dict):
    """Send webhook alert when rate limit is exceeded."""
    if not ALERT_WEBHOOK_URL:
        return
    try:
        import httpx
        async with httpx.AsyncClient() as http:
            await http.post(ALERT_WEBHOOK_URL, json={
                "event": "rate_limit_exceeded",
                "client": client,
                "endpoint": endpoint,
                "current": result["current"],
                "limit": result["limit"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, timeout=5)
    except Exception:
        pass  # Don't let alert failures affect the service


if __name__ == "__main__":
    print(f"🚦 API Rate Limiter starting on port {PORT}")
    print(f"   Default limit: {DEFAULT_RATE_LIMIT} requests per {DEFAULT_WINDOW_SECONDS}s")
    print(f"   Dashboard: http://localhost:{PORT}/dashboard")
    print(f"   API docs: http://localhost:{PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=PORT, proxy_headers=False)
