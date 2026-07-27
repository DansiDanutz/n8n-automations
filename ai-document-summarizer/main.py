#!/usr/bin/env python3
"""
AI Document Summarizer API
Upload documents (PDF, DOCX, TXT, CSV) and get AI-powered summaries,
key points, action items, and Q&A capabilities.
"""

import os
import io
import json
import hashlib
import hmac
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024
DB_PATH = os.getenv("DB_PATH", "./summaries.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def required_secret(name: str, minimum_length: int) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length or value == "replace-with-at-least-32-random-characters":
        raise RuntimeError(f"{name} must be at least {minimum_length} characters")
    return value


api_key = required_secret("API_KEY", 32)

# ─── OpenAI Client ───
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    client = None

# ─── Document Parsers ───
def parse_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")

def parse_csv(content: bytes) -> str:
    import csv
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if len(rows) > 100:
        rows = rows[:100]
    return "\n".join([", ".join(row) for row in rows])

def parse_pdf(content: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages[:50]:  # Max 50 pages
            text += page.extract_text() or ""
        return text
    except ImportError:
        return "[PDF parsing requires pypdf: pip install pypdf]"

def parse_docx(content: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([p.text for p in doc.paragraphs])
    except ImportError:
        return "[DOCX parsing requires python-docx: pip install python-docx]"

PARSERS = {
    "text/plain": parse_txt,
    "text/csv": parse_csv,
    "application/pdf": parse_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
    ".txt": parse_txt,
    ".csv": parse_csv,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}

# ─── Database ───
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE,
            file_size INTEGER,
            content_preview TEXT,
            word_count INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER REFERENCES documents(id),
            summary_type TEXT DEFAULT 'standard',
            summary TEXT,
            key_points TEXT,
            action_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER REFERENCES documents(id),
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── AI Functions ───
def ai_summarize(text: str, style: str = "concise", max_length: int = 500) -> dict:
    if not client:
        return {
            "summary": f"[Demo mode - no API key] Document has {len(text.split())} words. Set OPENAI_API_KEY for real summaries.",
            "key_points": ["Configure OPENAI_API_KEY in .env", "Restart the server", "Upload document again"],
            "action_items": ["Set up OpenAI API key"],
        }
    
    prompt = f"""Analyze this document and provide:
1. A {style} summary (max {max_length} words)
2. Key points (bullet list, max 7)
3. Action items if any (bullet list)

Respond in JSON format:
{{"summary": "...", "key_points": ["..."], "action_items": ["..."]}}

Document:
{text[:8000]}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    
    return json.loads(response.choices[0].message.content)

def ai_answer(text: str, question: str) -> str:
    if not client:
        return f"[Demo mode] Your question: '{question}'. Set OPENAI_API_KEY for real answers."
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"Answer questions about this document:\n{text[:6000]}"},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

# ─── Models ───
class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)

# ─── App ───
app = FastAPI(
    title="AI Document Summarizer",
    description="Upload documents and get AI-powered summaries, key points, action items, and Q&A.",
    version="1.0.0",
)


@app.middleware("http")
async def authenticate_documents(request: Request, call_next):
    if request.method != "OPTIONS" and request.url.path not in {"/", "/health"}:
        provided_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(provided_key, api_key):
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
    return await call_next(request)


allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    """Service info."""
    return {
        "service": "AI Document Summarizer",
        "version": "1.0.0",
        "status": "running",
        "supported_formats": [".txt", ".csv", ".pdf", ".docx"],
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing."""
    content = await file.read(MAX_FILE_SIZE + 1)
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    original_name = Path((file.filename or "upload").replace("\\", "/")).name
    ext = Path(original_name).suffix.lower()
    parser = PARSERS.get(ext) or PARSERS.get(file.content_type)
    
    if not parser:
        raise HTTPException(400, f"Unsupported format: {ext}. Supported: .txt, .csv, .pdf, .docx")
    
    text = parser(content)
    if not text.strip():
        raise HTTPException(400, "Could not extract text from document")
    
    file_hash = hashlib.sha256(content).hexdigest()
    word_count = len(text.split())
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO documents (filename, file_hash, file_size, content_preview, word_count) VALUES (?, ?, ?, ?, ?)",
            (original_name, file_hash, len(content), text[:500], word_count)
        )
        conn.commit()
        doc_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Document content already uploaded")
    finally:
        conn.close()
    
    # Save file
    save_path = Path(UPLOAD_DIR) / f"{doc_id}{ext}"
    with save_path.open("wb") as f:
        f.write(content)
    
    return {
        "document_id": doc_id,
        "filename": original_name,
        "file_size_bytes": len(content),
        "word_count": word_count,
        "preview": text[:300] + "..." if len(text) > 300 else text,
        "message": "Document uploaded. Use POST /summarize/{document_id} to generate summary.",
    }

@app.post("/summarize/{document_id}")
async def summarize_document(
    document_id: int,
    style: str = Query("concise", enum=["concise", "detailed", "bullet-points", "executive"]),
    max_length: int = Query(500, ge=50, le=2000),
):
    """Generate AI summary for an uploaded document."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT filename, content_preview, word_count FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Document not found")
    
    filename, content, word_count = row
    
    # Get full text from file
    files = list(Path(UPLOAD_DIR).glob(f"{document_id}.*"))
    if files:
        ext = files[0].suffix.lower()
        parser = PARSERS.get(ext, parse_txt)
        content = parser(files[0].read_bytes())
    
    result = ai_summarize(content, style, max_length)
    
    # Save summary
    conn.execute(
        "INSERT INTO summaries (document_id, summary_type, summary, key_points, action_items) VALUES (?, ?, ?, ?, ?)",
        (document_id, style, result["summary"], json.dumps(result.get("key_points", [])), json.dumps(result.get("action_items", [])))
    )
    conn.commit()
    conn.close()
    
    return {
        "document_id": document_id,
        "filename": filename,
        "word_count": word_count,
        "style": style,
        "summary": result["summary"],
        "key_points": result.get("key_points", []),
        "action_items": result.get("action_items", []),
    }

@app.post("/ask/{document_id}")
async def ask_question(document_id: int, req: QuestionRequest):
    """Ask a question about an uploaded document."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT filename FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Document not found")
    
    files = list(Path(UPLOAD_DIR).glob(f"{document_id}.*"))
    if not files:
        conn.close()
        raise HTTPException(404, "Document file not found")
    
    ext = files[0].suffix.lower()
    parser = PARSERS.get(ext, parse_txt)
    content = parser(files[0].read_bytes())
    
    answer = ai_answer(content, req.question)
    
    conn.execute(
        "INSERT INTO qa_history (document_id, question, answer) VALUES (?, ?, ?)",
        (document_id, req.question, answer)
    )
    conn.commit()
    conn.close()
    
    return {
        "document_id": document_id,
        "question": req.question,
        "answer": answer,
    }

@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, filename, file_size, word_count, uploaded_at FROM documents ORDER BY id DESC").fetchall()
    conn.close()
    
    return {
        "documents": [
            {"id": r[0], "filename": r[1], "file_size_bytes": r[2], "word_count": r[3], "uploaded_at": r[4]}
            for r in rows
        ],
        "total": len(rows),
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get document details with all summaries and Q&A history."""
    conn = sqlite3.connect(DB_PATH)
    doc = conn.execute("SELECT id, filename, file_size, word_count, content_preview, uploaded_at FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not doc:
        conn.close()
        raise HTTPException(404, "Document not found")
    
    summaries = conn.execute("SELECT id, summary_type, summary, key_points, action_items, created_at FROM summaries WHERE document_id = ? ORDER BY id DESC", (document_id,)).fetchall()
    qa = conn.execute("SELECT question, answer, created_at FROM qa_history WHERE document_id = ? ORDER BY id DESC LIMIT 20", (document_id,)).fetchall()
    conn.close()
    
    return {
        "id": doc[0], "filename": doc[1], "file_size_bytes": doc[2],
        "word_count": doc[3], "preview": doc[4], "uploaded_at": doc[5],
        "summaries": [
            {"id": s[0], "type": s[1], "summary": s[2], "key_points": json.loads(s[3] or "[]"), "action_items": json.loads(s[4] or "[]"), "created_at": s[5]}
            for s in summaries
        ],
        "qa_history": [{"question": q[0], "answer": q[1], "created_at": q[2]} for q in qa],
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and its summaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM qa_history WHERE document_id = ?", (document_id,))
    conn.execute("DELETE FROM summaries WHERE document_id = ?", (document_id,))
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()
    conn.close()
    
    for f in Path(UPLOAD_DIR).glob(f"{document_id}.*"):
        f.unlink()
    
    return {"status": "deleted", "document_id": document_id}

@app.get("/stats")
async def stats():
    """Get usage statistics."""
    conn = sqlite3.connect(DB_PATH)
    docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    sums = conn.execute("SELECT COUNT(*) FROM summaries").fetchone()[0]
    qas = conn.execute("SELECT COUNT(*) FROM qa_history").fetchone()[0]
    total_words = conn.execute("SELECT COALESCE(SUM(word_count), 0) FROM documents").fetchone()[0]
    conn.close()
    
    return {
        "total_documents": docs,
        "total_summaries": sums,
        "total_questions": qas,
        "total_words_processed": total_words,
    }


if __name__ == "__main__":
    print(f"📄 AI Document Summarizer starting on port {PORT}")
    print(f"   AI configured: {client is not None}")
    print(f"   Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"   API docs: http://localhost:{PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
