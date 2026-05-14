FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner

RUN addgroup --system --gid 1001 bot && adduser --system --uid 1001 bot

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .
RUN mkdir -p logs reports && chown -R bot:bot /app

USER bot

CMD ["python", "bot.py"]
