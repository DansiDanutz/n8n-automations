FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF generation
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libffi-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p templates

# Set environment variables
ENV PORT=8000
ENV DB_PATH=/app/invoices.db
ENV COMPANY_NAME="Your Company"
ENV COMPANY_ADDRESS="123 Business St, City, State 12345"
ENV COMPANY_EMAIL="billing@company.com"
ENV DEFAULT_CURRENCY="USD"
ENV DEFAULT_TAX_RATE="0.0"

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000')" || exit 1

# Run the application
CMD ["python3", "main.py"]