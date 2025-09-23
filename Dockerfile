# CBS Parts System - Complete Docker Image
FROM node:20-alpine

# Install Python and system dependencies (minimal)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nginx \
    supervisor \
    curl \
    && ln -sf python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy package files first for better Docker caching
COPY cbs_pdf_generator/package*.json ./cbs_pdf_generator/
COPY requirements.txt ./

# Install Python dependencies in virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies (including dev dependencies for build)
RUN cd cbs_pdf_generator && npm install

# Copy application code
COPY . .

# Copy configuration files
COPY deployment/nginx-docker.conf /etc/nginx/nginx.conf
COPY deployment/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories and make scripts executable
RUN mkdir -p /app/logs /var/log/supervisor /run/nginx && \
    chmod +x /app/scripts/*.py

# Skip React build for now - run in dev mode
# RUN cd cbs_pdf_generator && npm run build

# Set environment variables for production
ENV NODE_ENV=production
ENV PORT=5173
ENV HOST=0.0.0.0

# Expose ports
EXPOSE 80 443 8000 8002 8003 5173

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
    CMD curl -f http://localhost/health || curl -f http://localhost:8000/health || exit 1

# Create startup script with memory limits
RUN echo '#!/bin/sh' > /startup.sh && \
    echo 'export NODE_OPTIONS="--max-old-space-size=1024"' >> /startup.sh && \
    echo 'export PYTHONUNBUFFERED=1' >> /startup.sh && \
    echo 'ulimit -n 65536' >> /startup.sh && \
    echo 'exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' >> /startup.sh && \
    chmod +x /startup.sh

# Start with memory-optimized settings
CMD ["/startup.sh"]
