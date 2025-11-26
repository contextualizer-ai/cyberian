#!/bin/bash
# Example: Monitor status of all agents in a farm

set -e

BASE_PORT="${1:-4000}"
NUM_AGENTS="${2:-3}"

echo "Monitoring agent farm (ports $BASE_PORT - $((BASE_PORT+NUM_AGENTS-1)))"
echo ""

while true; do
  clear
  echo "=== Agent Farm Status ($(date)) ==="
  echo ""

  for ((i=0; i<NUM_AGENTS; i++)); do
    PORT=$((BASE_PORT+i))
    echo "Agent $((i+1)) (port $PORT):"

    if cyberian status --port "$PORT" 2>/dev/null; then
      echo "  Status: Running"
      echo "  Last message:"
      cyberian messages --last 1 --port "$PORT" 2>/dev/null | head -20
    else
      echo "  Status: Not running"
    fi

    echo ""
  done

  echo "Press Ctrl+C to stop monitoring"
  sleep 5
done
