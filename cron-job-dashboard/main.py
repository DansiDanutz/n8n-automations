#!/usr/bin/env python3
"""
Cron Job Dashboard
A visual dashboard and API for managing, monitoring, and debugging scheduled tasks.
"""

import os
import json
import sqlite3
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
DB_PATH = os.getenv("DB_PATH", "./cron_jobs.db")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "100"))
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# ─── Database ───
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            schedule TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            timeout_seconds INTEGER DEFAULT 300,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            last_status TEXT DEFAULT 'pending',
            last_duration_ms INTEGER DEFAULT 0,
            total_runs INTEGER DEFAULT 0,
            total_failures INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT REFERENCES jobs(id),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            status TEXT DEFAULT 'running',
            exit_code INTEGER,
            stdout TEXT DEFAULT '',
            stderr TEXT DEFAULT '',
            duration_ms INTEGER DEFAULT 0,
            retry_attempt INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Models ───
class JobCreate(BaseModel):
    name: str
    command: str
    schedule: str  # cron expression: "*/5 * * * *"
    description: Optional[str] = ""
    max_retries: int = 3
    timeout_seconds: int = 300

class JobUpdate(BaseModel):
    name: Optional[str] = None
    command: Optional[str] = None
    schedule: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None

# ─── Job Execution ───
def execute_job(job_id: str, command: str, timeout: int):
    """Execute a job and record results."""
    conn = sqlite3.connect(DB_PATH)
    start = time.time()
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        duration_ms = int((time.time() - start) * 1000)
        status = "success" if result.returncode == 0 else "failed"
        
        conn.execute("""
            INSERT INTO executions (job_id, finished_at, status, exit_code, stdout, stderr, duration_ms)
            VALUES (?, datetime('now'), ?, ?, ?, ?, ?)
        """, (job_id, status, result.returncode, result.stdout[-5000:], result.stderr[-2000:], duration_ms))
        
        conn.execute("""
            UPDATE jobs SET last_run_at = datetime('now'), last_status = ?, last_duration_ms = ?,
            total_runs = total_runs + 1, total_failures = total_failures + ? WHERE id = ?
        """, (status, duration_ms, 1 if status == "failed" else 0, job_id))
        
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start) * 1000)
        conn.execute("""
            INSERT INTO executions (job_id, finished_at, status, exit_code, stderr, duration_ms)
            VALUES (?, datetime('now'), 'timeout', -1, 'Command timed out', ?)
        """, (job_id, duration_ms))
        conn.execute("""
            UPDATE jobs SET last_run_at = datetime('now'), last_status = 'timeout',
            total_runs = total_runs + 1, total_failures = total_failures + 1 WHERE id = ?
        """, (job_id,))
    except Exception as e:
        conn.execute("""
            INSERT INTO executions (job_id, finished_at, status, stderr)
            VALUES (?, datetime('now'), 'error', ?)
        """, (job_id, str(e)))
    
    conn.commit()
    conn.close()

# ─── App ───
app = FastAPI(
    title="Cron Job Dashboard",
    description="Visual dashboard and API for managing scheduled tasks.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    """Service info."""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active'").fetchone()[0]
    conn.close()
    return {
        "service": "Cron Job Dashboard",
        "version": "1.0.0",
        "total_jobs": total,
        "active_jobs": active,
        "dashboard": "/dashboard",
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

@app.post("/jobs")
async def create_job(job: JobCreate):
    """Create a new cron job."""
    job_id = str(uuid.uuid4())[:8]
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO jobs (id, name, command, schedule, description, max_retries, timeout_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, job.name, job.command, job.schedule, job.description, job.max_retries, job.timeout_seconds))
    conn.commit()
    conn.close()
    
    return {"id": job_id, "name": job.name, "schedule": job.schedule, "status": "active"}

@app.get("/jobs")
async def list_jobs(status: Optional[str] = None):
    """List all cron jobs."""
    conn = sqlite3.connect(DB_PATH)
    if status:
        rows = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    conn.close()
    
    cols = ["id","name","command","schedule","description","status","retry_count","max_retries",
            "timeout_seconds","created_at","updated_at","last_run_at","next_run_at","last_status",
            "last_duration_ms","total_runs","total_failures"]
    
    return {"jobs": [dict(zip(cols, r)) for r in rows], "total": len(rows)}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job details with recent executions."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Job not found")
    
    cols = ["id","name","command","schedule","description","status","retry_count","max_retries",
            "timeout_seconds","created_at","updated_at","last_run_at","next_run_at","last_status",
            "last_duration_ms","total_runs","total_failures"]
    job = dict(zip(cols, row))
    
    execs = conn.execute("""
        SELECT id, started_at, finished_at, status, exit_code, duration_ms, retry_attempt
        FROM executions WHERE job_id = ? ORDER BY id DESC LIMIT 20
    """, (job_id,)).fetchall()
    conn.close()
    
    job["recent_executions"] = [
        {"id": e[0], "started_at": e[1], "finished_at": e[2], "status": e[3], "exit_code": e[4], "duration_ms": e[5], "retry": e[6]}
        for e in execs
    ]
    
    return job

@app.put("/jobs/{job_id}")
async def update_job(job_id: str, updates: JobUpdate):
    """Update a cron job."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Job not found")
    
    fields = {k: v for k, v in updates.dict().items() if v is not None}
    if not fields:
        raise HTTPException(400, "No fields to update")
    
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    conn.execute(f"UPDATE jobs SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return {"status": "updated", "job_id": job_id, "updated_fields": list(fields.keys())}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a cron job and its history."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM executions WHERE job_id = ?", (job_id,))
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "job_id": job_id}

@app.post("/jobs/{job_id}/run")
async def run_job(job_id: str, background_tasks: BackgroundTasks):
    """Manually trigger a job execution."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT command, timeout_seconds FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Job not found")
    conn.close()
    
    command, timeout = row
    background_tasks.add_task(execute_job, job_id, command, timeout)
    
    return {"status": "triggered", "job_id": job_id, "message": "Job is running in background"}

@app.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a job."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET status = 'paused' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "paused", "job_id": job_id}

@app.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused job."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET status = 'active' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "active", "job_id": job_id}

@app.get("/jobs/{job_id}/logs")
async def get_logs(job_id: str, limit: int = 10):
    """Get execution logs for a job."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, started_at, finished_at, status, exit_code, stdout, stderr, duration_ms
        FROM executions WHERE job_id = ? ORDER BY id DESC LIMIT ?
    """, (job_id, limit)).fetchall()
    conn.close()
    
    return {
        "job_id": job_id,
        "logs": [
            {"id": r[0], "started_at": r[1], "finished_at": r[2], "status": r[3],
             "exit_code": r[4], "stdout": r[5], "stderr": r[6], "duration_ms": r[7]}
            for r in rows
        ],
    }

@app.get("/stats")
async def global_stats():
    """Global statistics."""
    conn = sqlite3.connect(DB_PATH)
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    active_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active'").fetchone()[0]
    total_runs = conn.execute("SELECT COALESCE(SUM(total_runs), 0) FROM jobs").fetchone()[0]
    total_failures = conn.execute("SELECT COALESCE(SUM(total_failures), 0) FROM jobs").fetchone()[0]
    recent_execs = conn.execute("""
        SELECT j.name, e.status, e.duration_ms, e.started_at
        FROM executions e JOIN jobs j ON e.job_id = j.id
        ORDER BY e.id DESC LIMIT 10
    """).fetchall()
    conn.close()
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_executions": total_runs,
        "total_failures": total_failures,
        "success_rate": round((1 - total_failures / max(1, total_runs)) * 100, 1),
        "recent_activity": [
            {"job": r[0], "status": r[1], "duration_ms": r[2], "at": r[3]}
            for r in recent_execs
        ],
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Visual dashboard."""
    conn = sqlite3.connect(DB_PATH)
    jobs = conn.execute("SELECT id, name, schedule, status, last_status, last_run_at, total_runs, total_failures FROM jobs ORDER BY name").fetchall()
    total_runs = conn.execute("SELECT COALESCE(SUM(total_runs), 0) FROM jobs").fetchone()[0]
    total_failures = conn.execute("SELECT COALESCE(SUM(total_failures), 0) FROM jobs").fetchone()[0]
    conn.close()
    
    job_rows = ""
    for j in jobs:
        status_color = {"active": "#4caf50", "paused": "#ff9800", "disabled": "#666"}.get(j[3], "#666")
        run_color = {"success": "#4caf50", "failed": "#f44336", "timeout": "#ff9800", "pending": "#666"}.get(j[4], "#666")
        job_rows += f"""
        <tr>
            <td><code>{j[0]}</code></td>
            <td><strong>{j[1]}</strong></td>
            <td><code>{j[2]}</code></td>
            <td><span style="color:{status_color}">●</span> {j[3]}</td>
            <td><span style="color:{run_color}">●</span> {j[4]}</td>
            <td>{j[5] or 'Never'}</td>
            <td>{j[6]}</td>
            <td>{j[7]}</td>
            <td>
                <button onclick="fetch('/jobs/{j[0]}/run',{{method:'POST'}}).then(()=>location.reload())" style="padding:4px 8px;background:#2196f3;color:white;border:none;border-radius:4px;cursor:pointer">▶ Run</button>
            </td>
        </tr>"""
    
    success_rate = round((1 - total_failures / max(1, total_runs)) * 100, 1)
    
    return f"""<!DOCTYPE html>
<html><head><title>Cron Job Dashboard</title>
<meta http-equiv="refresh" content="10">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui;background:#0f0f23;color:#e0e0e0;padding:20px}}
h1{{color:#667eea;margin-bottom:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-bottom:30px}}
.card{{background:#1a1a3e;border-radius:12px;padding:20px;text-align:center}}
.card .value{{font-size:2rem;font-weight:bold;color:#667eea}}
.card .label{{color:#888;margin-top:5px;font-size:0.85rem}}
table{{width:100%;border-collapse:collapse;background:#1a1a3e;border-radius:12px;overflow:hidden}}
th{{background:#2a2a4e;padding:12px;text-align:left;font-size:0.85rem;color:#888}}
td{{padding:10px 12px;border-bottom:1px solid #2a2a4e;font-size:0.85rem}}
tr:hover td{{background:#252550}}
code{{background:#2a2a4e;padding:2px 6px;border-radius:4px;font-size:0.8rem}}
</style></head>
<body>
<h1>⏰ Cron Job Dashboard</h1>
<div class="grid">
<div class="card"><div class="value">{len(jobs)}</div><div class="label">Total Jobs</div></div>
<div class="card"><div class="value">{sum(1 for j in jobs if j[3]=='active')}</div><div class="label">Active</div></div>
<div class="card"><div class="value">{total_runs}</div><div class="label">Total Runs</div></div>
<div class="card"><div class="value">{success_rate}%</div><div class="label">Success Rate</div></div>
</div>
<table>
<tr><th>ID</th><th>Name</th><th>Schedule</th><th>Status</th><th>Last Run</th><th>Last Run At</th><th>Runs</th><th>Fails</th><th>Action</th></tr>
{job_rows}
</table>
<p style="margin-top:20px;color:#555;font-size:0.8rem">Auto-refreshes every 10s • API docs: <a href="/docs" style="color:#667eea">/docs</a></p>
</body></html>"""


if __name__ == "__main__":
    print(f"⏰ Cron Job Dashboard starting on port {PORT}")
    print(f"   Dashboard: http://localhost:{PORT}/dashboard")
    print(f"   API docs: http://localhost:{PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
