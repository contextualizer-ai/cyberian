#!/usr/bin/env python3
"""Cross-platform launcher for Cyberian Dashboard."""

import os
import subprocess
import sys
import time
import signal
from pathlib import Path

processes = []

def cleanup(signum=None, frame=None):
    """Clean up running processes."""
    print("\n🛑 Stopping dashboard...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    sys.exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_command(cmd, cwd, name):
    """Run a command and track the process."""
    print(f"Starting {name}...")
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True if sys.platform == "win32" else False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    processes.append(proc)
    return proc

def main():
    """Main launcher function."""
    print("🚀 Starting Cyberian Dashboard...")

    dashboard_dir = Path(__file__).parent
    backend_dir = dashboard_dir / "backend"
    frontend_dir = dashboard_dir / "frontend"

    # Start backend
    print("📦 Starting backend API server...")
    os.chdir(backend_dir)

    # Check if venv exists, create if not
    if not (backend_dir / ".venv").exists():
        print("Creating backend virtual environment...")
        subprocess.run(["uv", "venv"], check=True)

    # Install dependencies
    subprocess.run(["uv", "sync"], check=True)

    # Start backend server
    backend_cmd = ["uv", "run", "uvicorn", "main:app", "--reload", "--port", "8000"]
    run_command(backend_cmd, backend_dir, "Backend API")

    # Give backend time to start
    time.sleep(2)

    # Start frontend
    print("🎨 Starting frontend development server...")
    os.chdir(frontend_dir)

    # Check if node_modules exists, install if not
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], check=True)

    # Start frontend server
    frontend_cmd = ["npm", "run", "dev"]
    run_command(frontend_cmd, frontend_dir, "Frontend")

    print("\n✅ Dashboard is running!")
    print("   Backend API: http://localhost:8000")
    print("   Frontend:    http://localhost:3000")
    print("\nPress Ctrl+C to stop the dashboard\n")

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            for proc in processes:
                if proc.poll() is not None:
                    print("⚠️  A process has stopped unexpectedly")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()