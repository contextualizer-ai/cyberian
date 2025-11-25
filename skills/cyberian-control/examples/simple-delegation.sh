#!/bin/bash
# Example: Delegate a coding task to a remote agent

set -e

HOST="${1:-localhost}"
PORT="${2:-3284}"
TASK="${3:-Write a function to calculate fibonacci numbers}"

echo "Delegating task to agent at $HOST:$PORT"
echo "Task: $TASK"
echo ""

# Send task and wait for completion
cyberian message "$TASK" \
  --sync \
  --timeout 300 \
  --host "$HOST" \
  --port "$PORT"

echo ""
echo "Task completed. Retrieving last 10 messages..."
cyberian messages \
  --format yaml \
  --last 10 \
  --host "$HOST" \
  --port "$PORT"
