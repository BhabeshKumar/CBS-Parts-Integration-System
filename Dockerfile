# CBS Parts System - Complete Docker Image
FROM node:20-alpine

# Install Python and system dependencies (minimal)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nginx \
    supervisor \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
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

# Copy logo to templates directory for web server
RUN cp -r /app/logo /app/templates/logo

# Skip React build for now - run in dev mode
# RUN cd cbs_pdf_generator && npm run build

# Set environment variables for production
ENV NODE_ENV=production
ENV PORT=5173
ENV HOST=0.0.0.0
ENV VITE_API_URL=http://34.10.76.247:8003
ENV CBS_DOMAIN=34.10.76.247
ENV EMAIL_SMTP_HOST=smtp.gmail.com
ENV EMAIL_SMTP_PORT=587
ENV EMAIL_USERNAME=bhabesh.sheaney@gmail.com
ENV EMAIL_PASSWORD="arff dxli ejyd tubs"
ENV COMPANY_NAME="Concrete Batching Systems"
ENV SMARTSHEET_API_TOKEN=7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB
ENV CBS_PARTS_SHEET_ID=4695255724019588
ENV CBS_DISCOUNTS_SHEET_ID=8920011042148228
ENV ORDERS_INTAKE_SHEET_ID=p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1
ENV SALES_WORKS_ORDERS_SHEET_ID=G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391

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
