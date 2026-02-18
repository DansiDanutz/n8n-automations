#!/usr/bin/env python3
"""
Invoice Generator API
A FastAPI-based invoice generation system with PDF export capabilities.
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from decimal import Decimal
import uuid

from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager
from jinja2 import Template

# Try different PDF generation methods
try:
    from weasyprint import HTML, CSS
    PDF_METHOD = "weasyprint"
except ImportError:
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        PDF_METHOD = "reportlab"
    except ImportError:
        PDF_METHOD = "html"

# Configuration
DB_PATH = os.getenv("DB_PATH", "./invoices.db")
PORT = int(os.getenv("PORT", "8000"))
CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
TAX_RATE = float(os.getenv("DEFAULT_TAX_RATE", "0.0"))
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "123 Business St, City, State 12345")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "billing@company.com")

# Database setup
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            client_email TEXT,
            client_address TEXT,
            issue_date TEXT NOT NULL,
            due_date TEXT,
            currency TEXT DEFAULT 'USD',
            tax_rate REAL DEFAULT 0.0,
            subtotal REAL NOT NULL,
            tax_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'draft',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Invoice items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class InvoiceItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    line_total: Optional[float] = None

class InvoiceCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=200)
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    due_date: Optional[str] = None
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    tax_rate: float = Field(default=0.0, ge=0, le=1)
    items: List[InvoiceItem] = Field(..., min_items=1)
    notes: Optional[str] = None

class InvoiceUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    status: Optional[str] = Field(None, regex="^(draft|sent|paid|cancelled)$")
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    client_name: str
    client_email: Optional[str]
    client_address: Optional[str]
    issue_date: str
    due_date: Optional[str]
    currency: str
    tax_rate: float
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str
    notes: Optional[str]
    items: List[Dict[str, Any]]
    created_at: str
    updated_at: str

# Database helpers
def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_invoice_number() -> str:
    """Generate unique invoice number."""
    now = datetime.now()
    return f"INV-{now.year}-{now.month:02d}-{uuid.uuid4().hex[:8].upper()}"

def calculate_invoice_totals(items: List[InvoiceItem], tax_rate: float):
    """Calculate subtotal, tax, and total amounts."""
    subtotal = sum(item.quantity * item.unit_price for item in items)
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    return {
        "subtotal": round(subtotal, 2),
        "tax_amount": round(tax_amount, 2),
        "total_amount": round(total_amount, 2)
    }

def create_invoice_in_db(invoice_data: InvoiceCreate) -> int:
    """Create invoice in database and return ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate totals
    totals = calculate_invoice_totals(invoice_data.items, invoice_data.tax_rate)
    
    # Generate invoice number
    invoice_number = generate_invoice_number()
    issue_date = datetime.now().date().isoformat()
    
    # Insert invoice
    cursor.execute('''
        INSERT INTO invoices 
        (invoice_number, client_name, client_email, client_address, issue_date, 
         due_date, currency, tax_rate, subtotal, tax_amount, total_amount, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        invoice_number, invoice_data.client_name, invoice_data.client_email,
        invoice_data.client_address, issue_date, invoice_data.due_date,
        invoice_data.currency, invoice_data.tax_rate, totals["subtotal"],
        totals["tax_amount"], totals["total_amount"], invoice_data.notes
    ))
    
    invoice_id = cursor.lastrowid
    
    # Insert invoice items
    for item in invoice_data.items:
        line_total = item.quantity * item.unit_price
        cursor.execute('''
            INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, line_total)
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_id, item.description, item.quantity, item.unit_price, line_total))
    
    conn.commit()
    conn.close()
    
    return invoice_id

def get_invoice_with_items(invoice_id: int) -> Optional[Dict]:
    """Get invoice with items from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get invoice
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cursor.fetchone()
    
    if not invoice:
        conn.close()
        return None
    
    # Get items
    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    items = cursor.fetchall()
    
    conn.close()
    
    return {
        "invoice": dict(invoice),
        "items": [dict(item) for item in items]
    }

def generate_pdf_reportlab(invoice_data: Dict) -> bytes:
    """Generate PDF using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2E86C1')
    )
    story.append(Paragraph("INVOICE", title_style))
    
    # Invoice details
    invoice = invoice_data["invoice"]
    items = invoice_data["items"]
    
    # Company and invoice info
    company_info = f"""
    <b>{COMPANY_NAME}</b><br/>
    {COMPANY_ADDRESS}<br/>
    {COMPANY_EMAIL}
    """
    
    invoice_info = f"""
    <b>Invoice #:</b> {invoice['invoice_number']}<br/>
    <b>Issue Date:</b> {invoice['issue_date']}<br/>
    <b>Due Date:</b> {invoice['due_date'] or 'N/A'}<br/>
    <b>Status:</b> {invoice['status'].title()}
    """
    
    # Two column layout
    data = [
        [Paragraph(company_info, styles['Normal']), 
         Paragraph(invoice_info, styles['Normal'])]
    ]
    
    table = Table(data, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Bill to
    story.append(Paragraph(f"<b>Bill To:</b>", styles['Normal']))
    bill_to = f"{invoice['client_name']}<br/>"
    if invoice['client_email']:
        bill_to += f"{invoice['client_email']}<br/>"
    if invoice['client_address']:
        bill_to += f"{invoice['client_address']}"
    story.append(Paragraph(bill_to, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Items table
    items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
    for item in items:
        items_data.append([
            item['description'],
            str(item['quantity']),
            f"{invoice['currency']} {item['unit_price']:.2f}",
            f"{invoice['currency']} {item['line_total']:.2f}"
        ])
    
    # Add totals
    items_data.extend([
        ['', '', 'Subtotal:', f"{invoice['currency']} {invoice['subtotal']:.2f}"],
        ['', '', f'Tax ({invoice["tax_rate"]*100:.1f}%):', f"{invoice['currency']} {invoice['tax_amount']:.2f}"],
        ['', '', 'Total:', f"{invoice['currency']} {invoice['total_amount']:.2f}"]
    ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D5E8D4')),
    ]))
    
    story.append(items_table)
    
    if invoice['notes']:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        story.append(Paragraph(invoice['notes'], styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generate_pdf_weasyprint(invoice_data: Dict) -> bytes:
    """Generate PDF using WeasyPrint."""
    html_content = generate_invoice_html(invoice_data)
    pdf = HTML(string=html_content).write_pdf()
    return pdf

def generate_invoice_html(invoice_data: Dict) -> str:
    """Generate HTML invoice."""
    template_path = Path(__file__).parent / "templates" / "invoice.html"
    
    if template_path.exists():
        with open(template_path, 'r') as f:
            template_content = f.read()
    else:
        # Fallback inline template
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {{ invoice.invoice_number }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 3px solid #2E86C1; padding-bottom: 20px; margin-bottom: 30px; }
        .invoice-title { color: #2E86C1; font-size: 28px; margin: 0; }
        .company-info { float: left; width: 50%; }
        .invoice-info { float: right; width: 45%; text-align: right; }
        .clear { clear: both; }
        .bill-to { margin: 30px 0; }
        .items-table { width: 100%; border-collapse: collapse; margin: 30px 0; }
        .items-table th, .items-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .items-table th { background-color: #2E86C1; color: white; }
        .items-table .number { text-align: right; }
        .totals { float: right; width: 300px; }
        .total-row { font-weight: bold; background-color: #f9f9f9; }
        .notes { margin-top: 50px; }
        @media print { body { margin: 0; } }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="invoice-title">INVOICE</h1>
        <div class="company-info">
            <strong>{{ company_name }}</strong><br>
            {{ company_address }}<br>
            {{ company_email }}
        </div>
        <div class="invoice-info">
            <strong>Invoice #:</strong> {{ invoice.invoice_number }}<br>
            <strong>Issue Date:</strong> {{ invoice.issue_date }}<br>
            <strong>Due Date:</strong> {{ invoice.due_date or 'N/A' }}<br>
            <strong>Status:</strong> {{ invoice.status.title() }}
        </div>
        <div class="clear"></div>
    </div>

    <div class="bill-to">
        <strong>Bill To:</strong><br>
        {{ invoice.client_name }}<br>
        {% if invoice.client_email %}{{ invoice.client_email }}<br>{% endif %}
        {% if invoice.client_address %}{{ invoice.client_address }}{% endif %}
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th>Description</th>
                <th class="number">Quantity</th>
                <th class="number">Unit Price</th>
                <th class="number">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.description }}</td>
                <td class="number">{{ item.quantity }}</td>
                <td class="number">{{ invoice.currency }} {{ "%.2f"|format(item.unit_price) }}</td>
                <td class="number">{{ invoice.currency }} {{ "%.2f"|format(item.line_total) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totals">
        <table style="width: 100%;">
            <tr>
                <td><strong>Subtotal:</strong></td>
                <td class="number">{{ invoice.currency }} {{ "%.2f"|format(invoice.subtotal) }}</td>
            </tr>
            <tr>
                <td><strong>Tax ({{ "%.1f"|format(invoice.tax_rate * 100) }}%):</strong></td>
                <td class="number">{{ invoice.currency }} {{ "%.2f"|format(invoice.tax_amount) }}</td>
            </tr>
            <tr class="total-row">
                <td><strong>Total:</strong></td>
                <td class="number"><strong>{{ invoice.currency }} {{ "%.2f"|format(invoice.total_amount) }}</strong></td>
            </tr>
        </table>
    </div>

    {% if invoice.notes %}
    <div class="notes">
        <strong>Notes:</strong><br>
        {{ invoice.notes }}
    </div>
    {% endif %}
</body>
</html>
        """
    
    template = Template(template_content)
    return template.render(
        invoice=invoice_data["invoice"],
        items=invoice_data["items"],
        company_name=COMPANY_NAME,
        company_address=COMPANY_ADDRESS,
        company_email=COMPANY_EMAIL
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    # Create templates directory
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    yield
    # Shutdown (cleanup if needed)

# FastAPI app
app = FastAPI(
    title="Invoice Generator API",
    description="Professional invoice generation API with PDF export",
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

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Invoice Generator API is running",
        "status": "healthy",
        "pdf_method": PDF_METHOD,
        "version": "1.0.0"
    }

@app.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate):
    """Create a new invoice."""
    try:
        invoice_id = create_invoice_in_db(invoice_data)
        invoice_with_items = get_invoice_with_items(invoice_id)
        
        if not invoice_with_items:
            raise HTTPException(status_code=500, detail="Failed to create invoice")
        
        return InvoiceResponse(
            **invoice_with_items["invoice"],
            items=invoice_with_items["items"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int):
    """Get a specific invoice by ID."""
    invoice_with_items = get_invoice_with_items(invoice_id)
    
    if not invoice_with_items:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse(
        **invoice_with_items["invoice"],
        items=invoice_with_items["items"]
    )

@app.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: int):
    """Generate and return invoice as PDF."""
    invoice_with_items = get_invoice_with_items(invoice_id)
    
    if not invoice_with_items:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    try:
        if PDF_METHOD == "weasyprint":
            pdf_content = generate_pdf_weasyprint(invoice_with_items)
        elif PDF_METHOD == "reportlab":
            pdf_content = generate_pdf_reportlab(invoice_with_items)
        else:
            # Fallback to HTML
            html_content = generate_invoice_html(invoice_with_items)
            return HTMLResponse(content=html_content)
        
        invoice_number = invoice_with_items["invoice"]["invoice_number"]
        filename = f"invoice_{invoice_number}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/invoices/{invoice_id}/html")
async def get_invoice_html(invoice_id: int):
    """Get invoice as HTML (useful for preview or fallback)."""
    invoice_with_items = get_invoice_with_items(invoice_id)
    
    if not invoice_with_items:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    html_content = generate_invoice_html(invoice_with_items)
    return HTMLResponse(content=html_content)

@app.get("/invoices")
async def list_invoices(
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List invoices with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM invoices"
    params = []
    conditions = []
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if client_name:
        conditions.append("client_name LIKE ?")
        params.append(f"%{client_name}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    invoices = cursor.fetchall()
    conn.close()
    
    return {"invoices": [dict(invoice) for invoice in invoices]}

@app.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: int, update_data: InvoiceUpdate):
    """Update an existing invoice."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if invoice exists
    cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Build update query
    update_fields = []
    params = []
    
    for field, value in update_data.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = ?")
            params.append(value)
    
    if not update_fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(invoice_id)
    
    query = f"UPDATE invoices SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    
    return {"message": "Invoice updated successfully"}

@app.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int):
    """Delete an invoice."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Invoice deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )