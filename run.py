"""Unified dev runner — starts both FastAPI and Vite with a single command."""

import os
import signal
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def main():
    mode = "dev"
    if "--prod" in sys.argv:
        mode = "prod"

    processes = []

    try:
        if mode == "prod":
            print("\n  Anime Subtitle Companion — Production Mode")
            print("  Building frontend...")
            subprocess.run(
                ["npm", "run", "build"],
                cwd=str(FRONTEND_DIR),
                shell=True,
                check=True,
            )
            print("  Starting server on http://localhost:8000\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(BACKEND_DIR),
                shell=True,
            )
            processes.append(proc)
        else:
            print("\n  Anime Subtitle Companion — Dev Mode")
            print("  Backend:  http://localhost:8000")
            print("  Frontend: http://localhost:5173\n")

            backend_proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(BACKEND_DIR),
                shell=True,
            )
            processes.append(backend_proc)

            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(FRONTEND_DIR),
                shell=True,
            )
            processes.append(frontend_proc)

        # Wait for any process to exit
        while True:
            for proc in processes:
                ret = proc.poll()
                if ret is not None:
                    raise SystemExit(ret)
            try:
                processes[0].wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

    except (KeyboardInterrupt, SystemExit):
        print("\n  Shutting down...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    main()
