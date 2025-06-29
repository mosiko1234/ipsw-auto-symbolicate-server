FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    wget \
    build-essential \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ipsw CLI
RUN IPSW_VERSION=$(curl -s https://api.github.com/repos/blacktop/ipsw/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    echo "Downloading ipsw version: ${IPSW_VERSION}" && \
    curl -sL "https://github.com/blacktop/ipsw/releases/download/${IPSW_VERSION}/ipsw_${IPSW_VERSION#v}_linux_x86_64.tar.gz" -o ipsw.tar.gz && \
    tar -xzf ipsw.tar.gz && \
    mv ipsw /usr/local/bin/ && \
    rm ipsw.tar.gz && \
    chmod +x /usr/local/bin/ipsw

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY simple_app.py ./app.py

# Copy ipsw config
COPY config.yml /app/config.yml

# Create directories for data
RUN mkdir -p /app/crashlogs /app/symbols /app/uploads

# Expose port
EXPOSE 3993

# Run the application with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3993", "app:app"] 