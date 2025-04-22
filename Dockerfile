# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose ports for Flask and Streamlit
EXPOSE 8000 8501

# Create startup script
COPY start.sh .
RUN chmod +x start.sh

# Set environment variables
ENV FLASK_APP=api/app.py
ENV FLASK_ENV=production

# Run both services
CMD ["./start.sh"] 