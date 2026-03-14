#!/bin/bash
set -e

TEMPER_PORT=${TEMPER_PORT:-8421}

# Start temper-ai in background
echo "Starting temper-ai on port $TEMPER_PORT..."
temper-ai serve \
    --host 0.0.0.0 \
    --port "$TEMPER_PORT" \
    --config-root /app/configs \
    --dev &

# Wait for health
echo "Waiting for temper-ai..."
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$TEMPER_PORT/api/health" > /dev/null 2>&1; then
        echo "temper-ai ready"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "temper-ai failed to start within 120s"
        exit 1
    fi
    sleep 2
done

# Start poller (foreground — if it exits, container stops)
echo "Starting poller..."
exec python /app/worker.py
