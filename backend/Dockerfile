FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8000

# Start server
# Bind to 0.0.0.0 so Railway/Render can route external traffic.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
