import os
import sys
import time
import signal
import subprocess
import argparse
import threading
from pathlib import Path
from typing import Optional
import uvicorn

PACKAGE_DIR: Path
PROJECT_DIR: Path
try:
    PACKAGE_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = PACKAGE_DIR.parent
except NameError:
    PROJECT_DIR = Path.cwd()
    PACKAGE_DIR = PROJECT_DIR / "mlxui"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

frontend_process: Optional[subprocess.Popen] = None
stop_event = threading.Event()

def signal_handler(sig, frame):
    global frontend_process
    print("\n[mlxui __main__] Signal received, initiating shutdown...", flush=True)
    if frontend_process and frontend_process.poll() is None:
        print("[mlxui __main__] Terminating frontend process...", flush=True)
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
            print("[mlxui __main__] Frontend process terminated.", flush=True)
        except subprocess.TimeoutExpired:
            print("[mlxui __main__] Frontend process did not terminate gracefully, killing.", flush=True)
            frontend_process.kill()
            frontend_process.wait()
            print("[mlxui __main__] Frontend process killed.", flush=True)
        frontend_process = None
    stop_event.set()
    print("[mlxui __main__] Shutdown signal processed. Uvicorn should now exit.", flush=True)

def start_backend(host: str, port: int, reload: bool):
    print(f"[mlxui __main__] Starting backend server on http://{host}:{port}...", flush=True)
    try:
        uvicorn.run(
            "mlxui.backend.server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            reload_dirs=[str(PACKAGE_DIR / "backend")] if reload else None
        )
        print("[mlxui __main__] Backend server has stopped.", flush=True)
    except SystemExit:
        print("[mlxui __main__] Backend server stopped via SystemExit.", flush=True)
    except ImportError as e:
        print(f"[mlxui __main__] Import Error starting backend: {e}", file=sys.stderr, flush=True)
        print("This might happen if dependencies are missing or the project structure is incorrect.", file=sys.stderr, flush=True)
        print("Try running `pip install -e .` from the project root directory.", file=sys.stderr, flush=True)
        stop_event.set()
        sys.exit(1)
    except Exception as e:
        print(f"[mlxui __main__] Error starting backend: {e}", file=sys.stderr, flush=True)
        stop_event.set()
        sys.exit(1)

def start_frontend_dev():
    global frontend_process
    frontend_dir = PROJECT_DIR / "frontend"
    package_json_path = frontend_dir / "package.json"
    node_modules_path = frontend_dir / "node_modules"

    if not package_json_path.exists():
        print(f"[Error] Frontend 'package.json' not found at {package_json_path}. Cannot start frontend.", file=sys.stderr, flush=True)
        return

    if not node_modules_path.is_dir():
        print("[mlxui __main__] 'node_modules' not found. Running 'npm install' in frontend directory...", flush=True)
        print("(This may take a few minutes...)", flush=True)
        try:
            npm_install_cmd = ["npm", "install"]
            print(f"[mlxui __main__] Executing: {' '.join(npm_install_cmd)} in {frontend_dir}", flush=True)
            install_result = subprocess.run(
                npm_install_cmd,
                cwd=frontend_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            print("[mlxui __main__] npm install completed.", flush=True)
            if install_result.stderr:
                 print(f"[mlxui __main__] npm install stderr:\n{install_result.stderr}", flush=True)
        except FileNotFoundError:
            print("Error: 'npm' command not found. Please ensure Node.js and npm are installed and in your system's PATH.", file=sys.stderr, flush=True)
            return
        except subprocess.TimeoutExpired:
            print("Error: 'npm install' timed out. Please check your network connection and try running it manually.", file=sys.stderr, flush=True)
            return
        except subprocess.CalledProcessError as e:
            print(f"Error during 'npm install' (return code {e.returncode}):", file=sys.stderr, flush=True)
            print(f"stderr:\n{e.stderr}", flush=True)
            print("Please run 'npm install' manually in the 'frontend' directory.", file=sys.stderr, flush=True)
            return
        except Exception as e:
            print(f"An unexpected error occurred during npm install: {e}", file=sys.stderr, flush=True)
            return

    print("[mlxui __main__] Starting frontend development server (npm run dev)...", flush=True)
    try:
        npm_start_cmd = ["npm", "run", "dev"]
        print(f"[mlxui __main__] Executing: {' '.join(npm_start_cmd)} in {frontend_dir}", flush=True)
        frontend_process = subprocess.Popen(
            npm_start_cmd,
            cwd=frontend_dir,
        )
        time.sleep(5)
        if frontend_process.poll() is not None:
            print("Error: Frontend process terminated unexpectedly after start.", file=sys.stderr, flush=True)
            frontend_process = None
            return
        print(f"[mlxui __main__] Frontend Dev Server presumed running. Access typically at: http://localhost:3000 (or Vite's configured port)", flush=True)
    except FileNotFoundError:
        print("Error: 'npm' command not found for starting frontend.", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Error starting frontend: {e}", file=sys.stderr, flush=True)

def main():
    parser = argparse.ArgumentParser(description="Run the mlxui application.")
    parser.add_argument(
        "--host", type=str, default=os.getenv("MLXUI_HOST", "127.0.0.1"), help="Host for the backend server."
    )
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("MLXUI_PORT", "8000")), help="Port for the backend server."
    )
    parser.add_argument(
        "--no-frontend", action="store_true", help="Do not start the frontend development server."
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for the backend server (for development)."
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    fe_thread = None
    if not args.no_frontend:
        fe_thread = threading.Thread(target=start_frontend_dev, daemon=True)
        fe_thread.start()
        print("[mlxui __main__] Waiting for frontend to initialize...", flush=True)
        time.sleep(10 if not (PROJECT_DIR / "frontend" / "node_modules").is_dir() else 5)

    try:
        start_backend(args.host, args.port, args.reload)
    finally:
        print("[mlxui __main__] Backend has exited. Finalizing cleanup...", flush=True)
        stop_event.set()

        if frontend_process and frontend_process.poll() is None:
            print("[mlxui __main__] Ensuring frontend process is terminated...", flush=True)
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
                frontend_process.wait()
            print("[mlxui __main__] Frontend process cleanup attempt complete.", flush=True)

        if fe_thread and fe_thread.is_alive():
             print("[mlxui __main__] Waiting for frontend thread to join...", flush=True)
             fe_thread.join(timeout=2)
        print("[mlxui __main__] mlxui application shutdown complete.", flush=True)

if __name__ == "__main__":
    if "PROJECT_DIR" not in globals() or "PACKAGE_DIR" not in globals():
        print("Error: Project paths not defined. This script might not be in the expected location.", file=sys.stderr)
        sys.exit(1)
    main()
