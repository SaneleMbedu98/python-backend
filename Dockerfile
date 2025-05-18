# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /backend

# Copy requirements (create if not present)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest

COPY . .

ENV PYTHONPATH=/backend

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]