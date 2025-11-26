#!/bin/bash

# Simple launcher for NiceGUI dashboard

echo "🚀 Starting Cyberian NiceGUI Dashboard..."

# Check if we're in the right directory
if [ ! -f "nicegui_dashboard/dashboard.py" ]; then
    echo "❌ Error: Must run from cyberian root directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
uv sync --group dashboard

# Start the dashboard
echo "✨ Starting dashboard on http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""
uv run python nicegui_dashboard/dashboard.py