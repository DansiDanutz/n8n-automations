#!/usr/bin/env python3
"""
AI Customer Support Bot API
A FastAPI-based intelligent customer support system with OpenAI integration.
"""

import os
import sqlite3
import hmac
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI
import uvicorn
from contextlib import asynccontextmanager

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
KB_DIR = os.getenv("KB_DIR", "./knowledge_base")
DB_PATH = os.getenv("DB_PATH", "./support_bot.db")
PORT = int(os.getenv("PORT", "8000"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def required_secret(name: str, minimum_length: int) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length or value == "replace-with-at-least-32-random-characters":
        raise RuntimeError(f"{name} must be at least {minimum_length} characters")
    return value


api_key = required_secret("API_KEY", 32)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Database setup
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            satisfaction_rating INTEGER,
            feedback TEXT
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            message_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Knowledge base management
class KnowledgeBase:
    def __init__(self, kb_dir: str = KB_DIR):
        self.kb_dir = Path(kb_dir)
        self.knowledge = self.load_knowledge()
    
    def load_knowledge(self) -> str:
        """Load all markdown files from knowledge base directory."""
        if not self.kb_dir.exists():
            self.kb_dir.mkdir(parents=True, exist_ok=True)
            # Create sample FAQ
            sample_faq = """# Frequently Asked Questions

## Getting Started
**Q: How do I get started?**
A: Welcome! Simply ask your question and our AI will help you immediately.

## Account Issues
**Q: I forgot my password**
A: Click on 'Forgot Password' on the login page and follow the email instructions.

**Q: How do I update my profile?**
A: Go to Settings > Profile and update your information.

## Billing
**Q: How can I view my billing history?**
A: Navigate to Account > Billing to see all your invoices and payment history.

**Q: Can I change my payment method?**
A: Yes, go to Account > Billing > Payment Methods to add or update cards.

## Technical Support
**Q: The app is running slowly**
A: Try refreshing the page or clearing your browser cache. If issues persist, contact support.

## Contact
**Q: How can I reach human support?**
A: Type "human" or "agent" and we'll connect you with our support team.
"""
            with open(self.kb_dir / "faq.md", "w") as f:
                f.write(sample_faq)
        
        knowledge_content = ""
        for md_file in self.kb_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                knowledge_content += f"\n\n=== {md_file.name} ===\n\n"
                knowledge_content += f.read()
        
        return knowledge_content

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    sources_used: List[str] = Field(default_factory=list)
    needs_human: bool = False

class ConversationSummary(BaseModel):
    id: int
    user_id: str
    started_at: str
    last_message_at: str
    status: str
    message_count: int
    satisfaction_rating: Optional[int] = None

class FeedbackRequest(BaseModel):
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)

# Database helpers
def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def get_or_create_conversation(user_id: str, conversation_id: Optional[int] = None) -> int:
    """Get existing conversation or create new one."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if conversation_id:
        cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", 
                      (conversation_id, user_id))
        if cursor.fetchone():
            conn.close()
            return conversation_id
    
    # Create new conversation
    cursor.execute("INSERT INTO conversations (user_id) VALUES (?)", (user_id,))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return new_id

async def save_message(conversation_id: int, role: str, content: str) -> int:
    """Save message to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content)
    )
    message_id = cursor.lastrowid
    
    # Update conversation last_message_at
    cursor.execute(
        "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    
    conn.commit()
    conn.close()
    
    return message_id

async def generate_ai_response(message: str, conversation_history: List[Dict], kb: KnowledgeBase) -> tuple[str, bool]:
    """Generate AI response using OpenAI."""
    if not client:
        return "I'm sorry, but AI functionality is not configured. Please contact support.", True
    
    # Check for human escalation keywords
    escalation_keywords = ["human", "agent", "supervisor", "manager", "escalate", "frustrated", "angry"]
    if any(keyword in message.lower() for keyword in escalation_keywords):
        return "I'll connect you with a human agent right away. Please hold on.", True
    
    # Prepare context
    system_prompt = f"""You are a helpful customer support AI assistant. Use the following knowledge base to answer questions accurately and helpfully.

Knowledge Base:
{kb.knowledge}

Guidelines:
- Be friendly, professional, and helpful
- Use information from the knowledge base when relevant
- If you don't know something, admit it and suggest contacting human support
- Keep responses concise but complete
- If the customer seems frustrated, offer to escalate to human support
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 messages to avoid token limits)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content, False
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "I apologize, but I'm having technical difficulties. Let me connect you with a human agent.", True

# Initialize knowledge base
kb = KnowledgeBase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (cleanup if needed)

# FastAPI app
app = FastAPI(
    title="AI Customer Support Bot",
    description="Intelligent customer support API with AI-powered responses",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def authenticate_support_api(request: Request, call_next):
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
    return {"message": "AI Customer Support Bot is running", "status": "healthy"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage, background_tasks: BackgroundTasks):
    """Handle chat messages and generate AI responses."""
    # Get or create conversation
    conversation_id = await get_or_create_conversation(request.user_id, request.conversation_id)
    
    # Save user message
    await save_message(conversation_id, "user", request.message)
    
    # Get conversation history
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp",
        (conversation_id,)
    )
    history = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
    conn.close()
    
    # Generate AI response
    ai_response, needs_human = await generate_ai_response(request.message, history, kb)
    
    # Save AI response
    await save_message(conversation_id, "assistant", ai_response)
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        sources_used=["knowledge_base"],
        needs_human=needs_human
    )

@app.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    user_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """Get list of conversations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT c.*, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
    """
    params = []
    
    if user_id:
        query += " WHERE c.user_id = ?"
        params.append(user_id)
    
    query += " GROUP BY c.id ORDER BY c.last_message_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    conversations = []
    for row in rows:
        conversations.append(ConversationSummary(
            id=row["id"],
            user_id=row["user_id"],
            started_at=row["started_at"],
            last_message_at=row["last_message_at"],
            status=row["status"],
            message_count=row["message_count"],
            satisfaction_rating=row["satisfaction_rating"]
        ))
    
    return conversations

@app.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: int):
    """Get detailed conversation with all messages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get conversation
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
        (conversation_id,)
    )
    messages = cursor.fetchall()
    conn.close()
    
    return {
        "conversation": dict(conversation),
        "messages": [dict(msg) for msg in messages]
    }

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for conversation or specific message."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert feedback
    cursor.execute(
        "INSERT INTO feedback (conversation_id, message_id, rating, comment) VALUES (?, ?, ?, ?)",
        (feedback.conversation_id, feedback.message_id, feedback.rating, feedback.comment)
    )
    
    # Update conversation satisfaction if provided
    if feedback.conversation_id:
        cursor.execute(
            "UPDATE conversations SET satisfaction_rating = ? WHERE id = ?",
            (feedback.rating, feedback.conversation_id)
        )
    
    conn.commit()
    conn.close()
    
    return {"message": "Feedback submitted successfully"}

@app.get("/analytics")
async def get_analytics():
    """Get basic analytics about the support bot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total conversations
    cursor.execute("SELECT COUNT(*) as total FROM conversations")
    total_conversations = cursor.fetchone()["total"]
    
    # Active conversations (last 24 hours)
    cursor.execute(
        "SELECT COUNT(*) as active FROM conversations WHERE last_message_at > datetime('now', '-1 day')"
    )
    active_conversations = cursor.fetchone()["active"]
    
    # Average satisfaction rating
    cursor.execute("SELECT AVG(satisfaction_rating) as avg_rating FROM conversations WHERE satisfaction_rating IS NOT NULL")
    avg_rating = cursor.fetchone()["avg_rating"]
    
    # Total messages
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    total_messages = cursor.fetchone()["total"]
    
    conn.close()
    
    return {
        "total_conversations": total_conversations,
        "active_conversations_24h": active_conversations,
        "average_satisfaction_rating": round(avg_rating, 2) if avg_rating else None,
        "total_messages": total_messages
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
