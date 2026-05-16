# Multi-stage build for Python 3.11
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS runner

# Create non-root user for security
RUN groupadd --gid 1001 bot && \
    useradd --uid 1001 --gid bot --shell /bin/false bot

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/bot/.local
ENV PATH=/home/bot/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports data && \
    chown -R bot:bot /app /home/bot

# Switch to non-root user
USER bot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Default command
CMD ["python", "bot.py"]

# Labels
LABEL maintainer="Cesar Palacio"
LABEL version="2.0.0"
LABEL description="Gym Management Telegram Bot with Web Dashboard"