FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including ipsw CLI
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install ipsw CLI - Fix the download URL and use a more reliable method
RUN IPSW_VERSION=$(curl -s https://api.github.com/repos/blacktop/ipsw/releases/latest | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4 | tr -d 'v') && \
    curl -sL "https://github.com/blacktop/ipsw/releases/latest/download/ipsw_${IPSW_VERSION}_linux_x86_64.tar.gz" | tar -xz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/ipsw

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Copy ipsw config for container use
COPY config.docker.yml /app/ipsw.yml

# Set ipsw config environment variable
ENV IPSW_CONFIG=/app/ipsw.yml

# Create directories for data
RUN mkdir -p /app/crashlogs /app/symbols /app/uploads

# Expose port
EXPOSE 3993

# Run the application with Gunicorn (4 workers)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3993", "app:app"] 