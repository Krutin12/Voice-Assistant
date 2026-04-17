#!/usr/bin/env python3
"""
Wizard 3D Character - Desktop Application
Runs the 3D character viewer as a native desktop window using pywebview.

KEY ARCHITECTURE:
  - pywebview.start() MUST run on the main thread (it owns the GUI event loop)
  - The voice assistant loop runs in a background thread
  - WebSocket server pushes state updates to the Three.js frontend in real-time
"""

import sys
import os
import json
import threading
import time
import http.server
import socketserver
import asyncio
from pathlib import Path

# WebSocket support
try:
    import websockets
    import websockets.server
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

# pywebview for native desktop window
try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False


class CharacterState:
    """Character states"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    THINKING = "thinking"
    ERROR = "error"


class Character3DServer:
    """
    Manages:
      1. HTTP server for the Three.js frontend
      2. WebSocket server for real-time state updates
      3. Native desktop window via pywebview (MAIN THREAD)
    """

    def __init__(self, http_port=8770, ws_port=8769):
        self.http_port = http_port
        self.ws_port = ws_port
        self.state = CharacterState.IDLE
        self.status_text = "Initializing..."
        self.command_text = ""
        self._ws_clients = set()
        self._http_thread = None
        self._ws_thread = None
        self._ws_loop = None
        self._running = False
        self._window = None
        self._web_ui_dir = Path(__file__).parent / "web_ui"
        self._model_dir = Path(__file__).parent / "assets" / "character"
        self._voice_thread = None
        self._voice_fn = None

    def start(self):
        """Start internal HTTP + WebSocket servers in background threads"""
        if self._running:
            return
        self._running = True

        # Internal HTTP server (serves content to pywebview window)
        self._http_thread = threading.Thread(target=self._run_http_server, daemon=True)
        self._http_thread.start()

        # WebSocket server for real-time state push
        if HAS_WEBSOCKETS:
            self._ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
            self._ws_thread.start()

    def start_desktop_window(self, voice_fn=None):
        """
        Open the 3D character in a native desktop window.
        THIS IS A BLOCKING CALL — must be called from the main thread.
        
        Args:
            voice_fn: Optional callback that runs the voice assistant loop.
                      It will be started in a background thread AFTER the
                      window is created, so both run concurrently.
        """
        if not HAS_WEBVIEW:
            print("[!] pywebview not installed. Run: pip install pywebview")
            return

        self._voice_fn = voice_fn

        self._window = webview.create_window(
            'Wizard Voice Assistant',
            url=f'http://localhost:{self.http_port}',
            width=1000,
            height=700,
            resizable=True,
            frameless=False,
            easy_drag=True,
            background_color='#020208',
            text_select=False,
        )

        # When the window is fully loaded, start the voice assistant in background
        def on_loaded():
            if self._voice_fn and self._voice_thread is None:
                self._voice_thread = threading.Thread(
                    target=self._run_voice_loop,
                    daemon=True
                )
                self._voice_thread.start()

        self._window.events.loaded += on_loaded

        # This blocks until the window is closed
        webview.start(debug=False)

        # Window was closed — signal shutdown
        self._running = False

    def _run_voice_loop(self):
        """Wrapper to run the voice assistant function safely"""
        try:
            if self._voice_fn:
                self._voice_fn()
        except Exception as e:
            print(f"[!] Voice assistant error: {e}")

    def stop(self):
        """Stop servers and close window"""
        self._running = False
        if self._ws_loop:
            try:
                self._ws_loop.call_soon_threadsafe(self._ws_loop.stop)
            except Exception:
                pass
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass

    def set_state(self, state: str):
        """Update character state"""
        self.state = state
        self._broadcast({"state": state})

    def set_status_text(self, text: str):
        """Update status text"""
        self.status_text = text
        self._broadcast({"status": text})

    def set_command_text(self, text: str):
        """Update command text"""
        self.command_text = text
        self._broadcast({"command": text})

    def update(self, state: str = None, status: str = None, command: str = None):
        """Batch update"""
        msg = {}
        if state is not None:
            self.state = state
            msg["state"] = state
        if status is not None:
            self.status_text = status
            msg["status"] = status
        if command is not None:
            self.command_text = command
            msg["command"] = command
        if msg:
            self._broadcast(msg)

    def _broadcast(self, data: dict):
        """Send data to all connected WebSocket clients"""
        if not self._ws_loop or not self._ws_clients:
            return
        message = json.dumps(data)
        try:
            asyncio.run_coroutine_threadsafe(
                self._async_broadcast(message),
                self._ws_loop
            )
        except Exception:
            pass

    async def _async_broadcast(self, message: str):
        """Async broadcast"""
        disconnected = set()
        for client in self._ws_clients.copy():
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        self._ws_clients -= disconnected

    # ---------- HTTP Server ----------

    def _run_http_server(self):
        server = self

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(server._web_ui_dir), **kwargs)

            def do_GET(self):
                if self.path.startswith('/model/'):
                    model_name = self.path.split('/model/')[-1]
                    model_path = server._model_dir / model_name
                    if model_path.exists():
                        self.send_response(200)
                        self.send_header('Content-Type', 'model/gltf-binary')
                        self.send_header('Content-Length', str(model_path.stat().st_size))
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        with open(model_path, 'rb') as f:
                            self.wfile.write(f.read())
                        return
                    else:
                        self.send_error(404, f'Model not found: {model_name}')
                        return
                return super().do_GET()

            def log_message(self, format, *args):
                pass  # Suppress logs

        # Allow port reuse to prevent "address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("", self.http_port), Handler) as httpd:
                httpd.timeout = 1
                while self._running:
                    httpd.handle_request()
        except OSError as e:
            print(f"[!] HTTP server error (port {self.http_port}): {e}")

    # ---------- WebSocket Server ----------

    def _run_ws_server(self):
        self._ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._ws_loop)

        async def handler(websocket, path=None):
            self._ws_clients.add(websocket)
            try:
                await websocket.send(json.dumps({
                    "state": self.state,
                    "status": self.status_text,
                    "command": self.command_text,
                }))
                async for message in websocket:
                    pass
            except Exception:
                pass
            finally:
                self._ws_clients.discard(websocket)

        async def serve():
            try:
                try:
                    async with websockets.serve(handler, "localhost", self.ws_port):
                        while self._running:
                            await asyncio.sleep(0.5)
                except TypeError:
                    server = await websockets.server.serve(handler, "localhost", self.ws_port)
                    while self._running:
                        await asyncio.sleep(0.5)
                    server.close()
                    await server.wait_closed()
            except OSError as e:
                print(f"[!] WebSocket error (port {self.ws_port}): {e}")

        self._ws_loop.run_until_complete(serve())


def create_character_server(**kwargs):
    """Factory function"""
    return Character3DServer(**kwargs)


# ---- Standalone test / demo mode ----
if __name__ == "__main__":
    server = Character3DServer()
    server.start()

    # Run state demo in background
    def demo():
        time.sleep(4)
        print("-> LISTENING")
        server.update(state="listening", status="Listening to your command...")
        time.sleep(4)

        print("-> THINKING")
        server.update(state="thinking", status="Processing...", command="What is AI?")
        time.sleep(4)

        print("-> SPEAKING")
        server.update(state="speaking", status="Artificial intelligence is a branch of computer science...")
        time.sleep(6)

        print("-> IDLE")
        server.update(state="idle", status="Ready for commands", command="")
        time.sleep(3)

        print("-> SPEAKING (gestures)")
        server.update(state="speaking", status="Let me explain that in detail...", command="Tell me about machine learning")
        time.sleep(8)

        print("-> IDLE")
        server.update(state="idle", status="Ready for commands", command="")
        print("[OK] Demo complete!")

    # Start the demo in a background thread, and the window on main thread
    server.start_desktop_window(voice_fn=demo)
