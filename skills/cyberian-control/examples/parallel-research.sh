#!/bin/bash
# Example: Run parallel research tasks across multiple agents

set -e

QUERY="${1:-artificial intelligence}"
BASE_PORT="${2:-5000}"

echo "Running parallel research on: $QUERY"
echo "Using ports $BASE_PORT, $((BASE_PORT+1)), $((BASE_PORT+2))"
echo ""

# Send different aspects to different agents
echo "Sending task 1: Historical perspective..."
cyberian message "Research the history and evolution of $QUERY. Write findings to history.md. COMPLETION_STATUS: COMPLETE" \
  --sync --timeout 300 --port "$BASE_PORT" &

echo "Sending task 2: Current state..."
cyberian message "Research the current state of the art in $QUERY. Write findings to current.md. COMPLETION_STATUS: COMPLETE" \
  --sync --timeout 300 --port "$((BASE_PORT+1))" &

echo "Sending task 3: Future directions..."
cyberian message "Research future trends and predictions for $QUERY. Write findings to future.md. COMPLETION_STATUS: COMPLETE" \
  --sync --timeout 300 --port "$((BASE_PORT+2))" &

echo ""
echo "Waiting for all agents to complete..."
wait

echo ""
echo "All tasks completed!"
echo ""
echo "Agent 1 status:"
cyberian status --port "$BASE_PORT"

echo ""
echo "Agent 2 status:"
cyberian status --port "$((BASE_PORT+1))"

echo ""
echo "Agent 3 status:"
cyberian status --port "$((BASE_PORT+2))"
