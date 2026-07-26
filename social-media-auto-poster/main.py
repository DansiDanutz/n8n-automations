#!/usr/bin/env python3
"""
Social Media Auto-Poster API
A FastAPI-based social media automation system with scheduling capabilities.
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid
import hmac

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
import uvicorn
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import tweepy

# Configuration
DB_PATH = os.getenv("DB_PATH", "./social_media.db")
PORT = int(os.getenv("PORT", "8000"))


def required_secret(name: str, minimum_length: int) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length or value == "replace-with-at-least-32-random-characters":
        raise RuntimeError(f"{name} must be at least {minimum_length} characters")
    return value


api_key = required_secret("API_KEY", 32)

# Social Media API Keys (configured via environment)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_ID = os.getenv("LINKEDIN_PERSON_ID", "")

# Initialize scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{DB_PATH}')
}
executors = {
    'default': AsyncIOExecutor()
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'
)

# Database setup
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            platforms TEXT NOT NULL,
            media_urls TEXT,
            scheduled_time TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            error_message TEXT,
            engagement_metrics TEXT
        )
    ''')
    
    # Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            platform TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            metric_value INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        )
    ''')
    
    # Platform credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT UNIQUE NOT NULL,
            credentials TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Social Media Platform Adapters
class TwitterAdapter:
    def __init__(self):
        if TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET:
            self.client = tweepy.Client(
                bearer_token=TWITTER_BEARER_TOKEN,
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            self.is_configured = True
        else:
            self.client = None
            self.is_configured = False
    
    async def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {"success": False, "error": "Twitter not configured"}
        
        try:
            # For now, just post text (media upload would require more complex setup)
            response = self.client.create_tweet(text=content[:280])  # Twitter limit
            
            return {
                "success": True,
                "platform": "twitter",
                "post_id": response.data['id'],
                "url": f"https://twitter.com/user/status/{response.data['id']}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        if not self.is_configured:
            return {"likes": 0, "retweets": 0, "replies": 0}
        
        try:
            tweet = self.client.get_tweet(
                post_id, 
                tweet_fields=['public_metrics']
            )
            
            if tweet.data:
                metrics = tweet.data.public_metrics
                return {
                    "likes": metrics.get('like_count', 0),
                    "retweets": metrics.get('retweet_count', 0),
                    "replies": metrics.get('reply_count', 0),
                    "views": metrics.get('impression_count', 0)
                }
        except Exception as e:
            print(f"Error getting Twitter metrics: {e}")
        
        return {"likes": 0, "retweets": 0, "replies": 0, "views": 0}

class InstagramAdapter:
    def __init__(self):
        self.access_token = INSTAGRAM_ACCESS_TOKEN
        self.account_id = INSTAGRAM_ACCOUNT_ID
        self.is_configured = bool(self.access_token and self.account_id)
    
    async def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {"success": False, "error": "Instagram not configured (placeholder)"}
        
        # Instagram Basic Display API doesn't support posting
        # This would require Instagram Graph API and proper business account
        return {
            "success": False,
            "error": "Instagram posting requires Graph API setup - placeholder implementation"
        }
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        return {"likes": 0, "comments": 0, "shares": 0}

class LinkedInAdapter:
    def __init__(self):
        self.access_token = LINKEDIN_ACCESS_TOKEN
        self.person_id = LINKEDIN_PERSON_ID
        self.is_configured = bool(self.access_token and self.person_id)
    
    async def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {"success": False, "error": "LinkedIn not configured (placeholder)"}
        
        # LinkedIn API posting placeholder
        return {
            "success": False,
            "error": "LinkedIn posting requires OAuth 2.0 setup - placeholder implementation"
        }
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        return {"likes": 0, "comments": 0, "shares": 0}

# Platform manager
class SocialMediaManager:
    def __init__(self):
        self.adapters = {
            "twitter": TwitterAdapter(),
            "instagram": InstagramAdapter(),
            "linkedin": LinkedInAdapter()
        }
    
    async def post_to_platform(self, platform: str, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if platform not in self.adapters:
            return {"success": False, "error": f"Platform {platform} not supported"}
        
        return await self.adapters[platform].post(content, media_urls)
    
    async def get_platform_metrics(self, platform: str, post_id: str) -> Dict[str, Any]:
        if platform not in self.adapters:
            return {}
        
        return await self.adapters[platform].get_metrics(post_id)

# Initialize social media manager
sm_manager = SocialMediaManager()

# Pydantic models
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    platforms: List[str] = Field(..., min_length=1)
    media_urls: Optional[List[HttpUrl]] = None
    scheduled_time: Optional[str] = None  # ISO format datetime

class PostUpdate(BaseModel):
    content: Optional[str] = None
    platforms: Optional[List[str]] = None
    media_urls: Optional[List[HttpUrl]] = None
    scheduled_time: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|published|failed|cancelled)$")

class PostResponse(BaseModel):
    id: int
    post_id: str
    content: str
    platforms: List[str]
    media_urls: Optional[List[str]]
    scheduled_time: Optional[str]
    status: str
    created_at: str
    published_at: Optional[str]
    error_message: Optional[str]
    engagement_metrics: Optional[Dict[str, Any]]

class AnalyticsResponse(BaseModel):
    total_posts: int
    published_posts: int
    scheduled_posts: int
    failed_posts: int
    total_engagement: Dict[str, int]
    platform_breakdown: Dict[str, Dict[str, Any]]

# Database helpers
def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_post_id() -> str:
    """Generate unique post ID."""
    return f"post_{uuid.uuid4().hex[:12]}"

async def save_post_to_db(post_data: PostCreate) -> str:
    """Save post to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    post_id = generate_post_id()
    platforms_json = json.dumps(post_data.platforms)
    media_urls_json = json.dumps([str(url) for url in post_data.media_urls]) if post_data.media_urls else None
    
    cursor.execute('''
        INSERT INTO posts (post_id, content, platforms, media_urls, scheduled_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        post_id,
        post_data.content,
        platforms_json,
        media_urls_json,
        post_data.scheduled_time
    ))
    
    conn.commit()
    conn.close()
    
    return post_id

async def update_post_status(post_id: str, status: str, error_message: str = None, published_at: str = None):
    """Update post status in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE posts 
        SET status = ?, error_message = ?, published_at = ?
        WHERE post_id = ?
    ''', (status, error_message, published_at, post_id))
    
    conn.commit()
    conn.close()

async def get_post_from_db(post_id: str) -> Optional[Dict]:
    """Get post from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if post:
        post_dict = dict(post)
        post_dict['platforms'] = json.loads(post_dict['platforms'])
        if post_dict['media_urls']:
            post_dict['media_urls'] = json.loads(post_dict['media_urls'])
        return post_dict
    
    return None

async def publish_post_job(post_id: str):
    """Background job to publish a scheduled post."""
    post = await get_post_from_db(post_id)
    if not post:
        print(f"Post {post_id} not found")
        return
    
    if post['status'] != 'scheduled':
        print(f"Post {post_id} is not scheduled (status: {post['status']})")
        return
    
    print(f"Publishing post {post_id} to platforms: {post['platforms']}")
    
    results = []
    any_success = False
    errors = []
    
    for platform in post['platforms']:
        result = await sm_manager.post_to_platform(
            platform,
            post['content'],
            post['media_urls']
        )
        
        results.append({
            'platform': platform,
            'success': result['success'],
            'error': result.get('error'),
            'post_id': result.get('post_id'),
            'url': result.get('url')
        })
        
        if result['success']:
            any_success = True
        else:
            errors.append(f"{platform}: {result.get('error', 'Unknown error')}")
    
    # Update post status
    if any_success:
        await update_post_status(
            post_id,
            'published',
            '; '.join(errors) if errors else None,
            datetime.now(timezone.utc).isoformat()
        )
    else:
        await update_post_status(
            post_id,
            'failed',
            '; '.join(errors),
            None
        )
    
    print(f"Post {post_id} publication completed. Results: {results}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    scheduler.start()
    print("Social Media Auto-Poster started")
    print(f"Twitter configured: {sm_manager.adapters['twitter'].is_configured}")
    print(f"Instagram configured: {sm_manager.adapters['instagram'].is_configured}")
    print(f"LinkedIn configured: {sm_manager.adapters['linkedin'].is_configured}")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    print("Social Media Auto-Poster stopped")

# FastAPI app
app = FastAPI(
    title="Social Media Auto-Poster",
    description="Automated social media posting with scheduling capabilities",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def authenticate_control_plane(request: Request, call_next):
    if request.method != "OPTIONS" and request.url.path not in {"/", "/health"}:
        provided_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(provided_key, api_key):
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
    return await call_next(request)

# CORS middleware
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Social Media Auto-Poster is running",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate, background_tasks: BackgroundTasks):
    """Create a new social media post (scheduled or immediate)."""
    # Validate platforms
    supported_platforms = list(sm_manager.adapters.keys())
    invalid_platforms = [p for p in post_data.platforms if p not in supported_platforms]
    
    if invalid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platforms: {invalid_platforms}. Supported: {supported_platforms}"
        )
    
    # Save to database
    post_id = await save_post_to_db(post_data)
    
    if post_data.scheduled_time:
        # Schedule the post
        try:
            scheduled_dt = datetime.fromisoformat(post_data.scheduled_time.replace('Z', '+00:00'))
            
            if scheduled_dt <= datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
            
            scheduler.add_job(
                publish_post_job,
                'date',
                run_date=scheduled_dt,
                args=[post_id],
                id=f"publish_{post_id}"
            )
            
            status = "scheduled"
        except ValueError as e:
            await update_post_status(post_id, "failed", f"Invalid datetime format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
        
    else:
        # Publish immediately
        background_tasks.add_task(publish_post_job, post_id)
        status = "publishing"
    
    # Get the created post
    post = await get_post_from_db(post_id)
    
    return PostResponse(**post)

@app.get("/posts", response_model=List[PostResponse])
async def list_posts(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List posts with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM posts"
    params = []
    conditions = []
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if platform:
        conditions.append("platforms LIKE ?")
        params.append(f"%{platform}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    posts = cursor.fetchall()
    conn.close()
    
    result = []
    for post in posts:
        post_dict = dict(post)
        post_dict['platforms'] = json.loads(post_dict['platforms'])
        if post_dict['media_urls']:
            post_dict['media_urls'] = json.loads(post_dict['media_urls'])
        result.append(PostResponse(**post_dict))
    
    return result

@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    """Get a specific post by ID."""
    post = await get_post_from_db(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return PostResponse(**post)

@app.post("/posts/{post_id}/publish")
async def publish_post_now(post_id: str, background_tasks: BackgroundTasks):
    """Publish a post immediately (cancel scheduling if needed)."""
    post = await get_post_from_db(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post['status'] not in ['scheduled', 'failed']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish post with status: {post['status']}"
        )
    
    # Cancel scheduled job if it exists
    try:
        scheduler.remove_job(f"publish_{post_id}")
    except:
        pass  # Job might not exist
    
    # Update status and publish
    await update_post_status(post_id, "publishing")
    background_tasks.add_task(publish_post_job, post_id)
    
    return {"message": "Post queued for immediate publishing"}

@app.delete("/posts/{post_id}")
async def cancel_post(post_id: str):
    """Cancel a scheduled post."""
    post = await get_post_from_db(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post['status'] == 'published':
        raise HTTPException(status_code=400, detail="Cannot cancel published post")
    
    # Remove scheduled job
    try:
        scheduler.remove_job(f"publish_{post_id}")
    except:
        pass  # Job might not exist
    
    # Update status
    await update_post_status(post_id, "cancelled")
    
    return {"message": "Post cancelled successfully"}

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get analytics and metrics for all posts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic counts
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    status_counts = dict(cursor.fetchall())
    
    # Platform breakdown
    cursor.execute("SELECT platforms, status, COUNT(*) as count FROM posts GROUP BY platforms, status")
    platform_data = cursor.fetchall()
    
    conn.close()
    
    # Process platform breakdown
    platform_breakdown = {}
    for row in platform_data:
        platforms = json.loads(row[0])  # Parse JSON
        for platform in platforms:
            if platform not in platform_breakdown:
                platform_breakdown[platform] = {"total": 0, "published": 0, "scheduled": 0, "failed": 0}
            
            platform_breakdown[platform]["total"] += row[2]
            if row[1] in platform_breakdown[platform]:
                platform_breakdown[platform][row[1]] += row[2]
    
    # Mock engagement data (in real implementation, fetch from platform APIs)
    total_engagement = {
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "views": 0
    }
    
    return AnalyticsResponse(
        total_posts=sum(status_counts.values()),
        published_posts=status_counts.get('published', 0),
        scheduled_posts=status_counts.get('scheduled', 0),
        failed_posts=status_counts.get('failed', 0),
        total_engagement=total_engagement,
        platform_breakdown=platform_breakdown
    )

@app.get("/platforms")
async def get_platform_status():
    """Get status of all configured platforms."""
    platforms = {}
    
    for name, adapter in sm_manager.adapters.items():
        platforms[name] = {
            "configured": adapter.is_configured,
            "status": "active" if adapter.is_configured else "not_configured"
        }
    
    return {"platforms": platforms}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
