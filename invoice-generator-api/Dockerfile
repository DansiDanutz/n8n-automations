FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2" \
    && python -m pip install --no-cache-dir -r requirements.txt

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
    CMD python3 -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python3", "main.py"]
