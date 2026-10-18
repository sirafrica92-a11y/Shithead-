"""Start the local-only Shithead browser preview with one Python command."""
from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser_when_ready() -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.25):
                webbrowser.open(URL)
                return
        except OSError:
            time.sleep(0.2)
    print(f"Could not confirm local server start. Check the console. {URL}")


def main() -> int:
    try:
        import fastapi  # noqa: F401
        import uvicorn
    except ImportError:
        print("Shithead needs Python dependencies first.")
        print(f"Run: {sys.executable} -m pip install -r requirements.txt")
        return 1
    print("Starting Shithead at", URL)
    print("Keep this window open while playing. Ctrl+C stops the server.")
    thread = threading.Thread(target=open_browser_when_ready, daemon=True)
    thread.start()
    uvicorn.run("server.app.main:app", host=HOST, port=PORT, workers=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
