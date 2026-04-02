#!/bin/bash
set -e

TEMPER_PORT=${TEMPER_PORT:-8421}

# Set up .netrc for Heroku git push auth (if API key is available)
if [ -n "$HEROKU_API_KEY" ]; then
    echo "machine git.heroku.com
  login heroku
  password $HEROKU_API_KEY" > /root/.netrc
    chmod 600 /root/.netrc
    echo "Heroku git auth configured"
fi

# Start temper-ai v0.1 server in background
echo "Starting temper serve on port $TEMPER_PORT..."
TEMPER_DATABASE_URL="${TEMPER_DATABASE_URL}" \
    VLLM_BASE_URL="${VLLM_BASE_URL:-http://localhost:8000}" \
    VLLM_MODEL="${VLLM_MODEL:-qwen3-next}" \
    temper serve --port "$TEMPER_PORT" --config-dir /app/configs &

# Wait for health
echo "Waiting for temper..."
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$TEMPER_PORT/api/health" > /dev/null 2>&1; then
        echo "temper ready"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "temper failed to start within 120s"
        exit 1
    fi
    sleep 2
done

# Start poller (foreground — if it exits, container stops)
echo "Starting worker..."
exec python /app/worker.py
