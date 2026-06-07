"""Stdlib HTTP server for Serenity Twin browser UI."""

from __future__ import annotations

import json
import mimetypes
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "ui"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from serenity_twin.llm import ENV_FILE, load_deepseek_key  # noqa: E402
from serenity_twin.paths import DATA, TWEETS_JSON  # noqa: E402
from serenity_twin.session_store import (  # noqa: E402
    create_session,
    get_session_messages,
    init_db,
    list_sessions,
    save_message,
)
from serenity_twin.tweets import load_archive  # noqa: E402
from serenity_twin.ui_chat import handle_prompt, handle_prompt_stream, run_lookup, run_radar  # noqa: E402
from serenity_twin.web_research import probe_web_available  # noqa: E402

init_db()

_CLIENT_GONE = (
    BrokenPipeError,
    ConnectionResetError,
    ConnectionAbortedError,
)


def _is_client_disconnect(exc: BaseException) -> bool:
    if isinstance(exc, _CLIENT_GONE):
        return True
    if isinstance(exc, OSError) and getattr(exc, "winerror", None) in (10053, 10054):
        return True
    return False


class SerenityUIHandler(BaseHTTPRequestHandler):
    server_version = "SerenityTwinUI/0.3"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_sse(self, event: str, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(f"event: {event}\n".encode())
        self.wfile.write(b"data: ")
        self.wfile.write(payload)
        self.wfile.write(b"\n\n")
        self.wfile.flush()

    def _safe_send_sse(self, event: str, data: dict) -> bool:
        """Return False if the browser closed the stream (cancel / navigate away)."""
        try:
            self._send_sse(event, data)
            return True
        except _CLIENT_GONE:
            return False
        except OSError as exc:
            if _is_client_disconnect(exc):
                return False
            raise

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            count = 0
            if TWEETS_JSON.exists():
                try:
                    count = len(load_archive(TWEETS_JSON))
                except Exception:
                    pass
            env_exists = ENV_FILE.exists()
            self._send_json(
                {
                    "corpus_tweets": count,
                    "deepseek_available": load_deepseek_key() is not None,
                    "live_web_available": probe_web_available(),
                    "auto_live_web": True,
                    "agent_parity": True,
                    "ui_version": "0.3.8",
                    "env_path": str(ENV_FILE),
                    "env_exists": env_exists,
                    "cursor_alternative": True,
                }
            )
            return

        if path == "/api/sessions":
            self._send_json({"sessions": list_sessions()})
            return

        if path.startswith("/api/sessions/") and path.count("/") == 3:
            sid = path.rsplit("/", 1)[-1]
            self._send_json({"session_id": sid, "messages": get_session_messages(sid)})
            return

        if path == "/api/prompts":
            prompts_file = UI_DIR / "prompts.json"
            data = json.loads(prompts_file.read_text(encoding="utf-8")) if prompts_file.exists() else []
            self._send_json({"prompts": data})
            return

        if path == "/api/community":
            links_file = UI_DIR / "links.json"
            data = json.loads(links_file.read_text(encoding="utf-8")) if links_file.exists() else {}
            self._send_json(data)
            return

        if path == "/i18n.json":
            i18n_file = UI_DIR / "i18n.json"
            if i18n_file.is_file():
                content = i18n_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404)
            return

        if path.startswith("/api/lookup/"):
            ticker = path.rsplit("/", 1)[-1].upper().lstrip("$")
            try:
                payload = run_lookup(ticker)
                self._send_json(payload)
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
            return

        if path == "/api/radar":
            qs = parse_qs(parsed.query)
            window = int(qs.get("window", ["14"])[0])
            top = int(qs.get("top", ["12"])[0])
            try:
                data, text = run_radar(window, top)
                self._send_json({"data": data, "text": text})
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
            return

        if path == "/api/daily-brief":
            latest = DATA / "daily-brief-latest.txt"
            text = latest.read_text(encoding="utf-8") if latest.exists() else ""
            self._send_json({"text": text, "exists": latest.exists()})
            return

        if path in ("/", ""):
            path = "/index.html"
        file_path = (UI_DIR / path.lstrip("/")).resolve()
        if not str(file_path).startswith(str(UI_DIR.resolve())):
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        ctype, _ = mimetypes.guess_type(str(file_path))
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/sessions":
            body = self._read_json_body()
            sess = create_session(body.get("title") or "New chat")
            self._send_json(sess)
            return

        if path == "/api/chat/stream":
            self._handle_chat_stream()
            return

        if path == "/api/chat":
            try:
                body = self._read_json_body()
                prompt = (body.get("prompt") or "").strip()
                if not prompt:
                    self._send_json({"error": "prompt required"}, 400)
                    return
                use_llm = load_deepseek_key() is not None
                result = handle_prompt(
                    prompt,
                    mode=body.get("mode"),
                    ticker=body.get("ticker"),
                    use_llm=use_llm,
                    locale=body.get("locale", "zh"),
                )
                sid = body.get("session_id")
                if sid:
                    save_message(
                        sid,
                        prompt=prompt,
                        mode=result.get("mode"),
                        ticker=result.get("ticker"),
                        html_snapshot=result.get("html", ""),
                        structured=result.get("structured"),
                        markdown=result.get("markdown", ""),
                        llm_narrative=result.get("llm_narrative", ""),
                    )
                    result["session_id"] = sid
                self._send_json(result)
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
            return

        self.send_error(404)

    def _handle_chat_stream(self) -> None:
        sse_open = False
        try:
            body = self._read_json_body()
            prompt = (body.get("prompt") or "").strip()
            if not prompt:
                self._send_json({"error": "prompt required"}, 400)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            sse_open = True

            final: dict | None = None
            use_llm = load_deepseek_key() is not None
            client_connected = True
            for event in handle_prompt_stream(
                prompt,
                mode=body.get("mode"),
                ticker=body.get("ticker"),
                use_llm=use_llm,
                locale=body.get("locale", "zh"),
            ):
                etype = event.get("type", "message")
                if etype == "done":
                    final = event.get("data")
                if not self._safe_send_sse(etype, event):
                    client_connected = False
                    break

            if not client_connected:
                return

            sid = body.get("session_id")
            if sid and final:
                save_message(
                    sid,
                    prompt=prompt,
                    mode=final.get("mode"),
                    ticker=final.get("ticker"),
                    html_snapshot=final.get("html", ""),
                    structured=final.get("structured"),
                    markdown=final.get("markdown", ""),
                    llm_narrative=final.get("llm_narrative", ""),
                )
                self._safe_send_sse("saved", {"session_id": sid})
        except Exception as exc:
            if _is_client_disconnect(exc):
                return
            if sse_open:
                if not self._safe_send_sse("error", {"message": str(exc)}):
                    return
            else:
                self._send_json({"error": str(exc)}, 500)


def open_cursor_simple_browser(url: str) -> bool:
    """Open URL in Cursor/VS Code Simple Browser (embedded preview pane)."""
    import shutil
    import urllib.parse

    encoded = urllib.parse.quote(url, safe="")
    uri = f"vscode://vscode.simple-browser/show?url={encoded}"
    for cmd in ("cursor", "code"):
        exe = shutil.which(cmd)
        if not exe:
            continue
        try:
            subprocess.Popen(
                [exe, "--open-url", uri],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except OSError:
            continue
    return False


def serve(
    host: str = "127.0.0.1",
    port: int = 17876,
    *,
    open_mode: str = "browser",
) -> int:
    """Start UI server. open_mode: browser | cursor | none."""
    server = ThreadingHTTPServer((host, port), SerenityUIHandler)
    bound = server.server_address[1]
    url = f"http://{host}:{bound}/"
    print(f"Serenity Twin UI → {url}")
    print("Press Ctrl+C to stop.")
    if open_mode == "browser":
        webbrowser.open(url)
    elif open_mode == "cursor":
        if open_cursor_simple_browser(url):
            print("Opened in Cursor Simple Browser (embedded preview).")
        else:
            print("Could not auto-open Cursor preview.")
            print("Manual: Ctrl+Shift+P → 'Simple Browser: Show' → paste:")
            print(f"  {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
    return bound


def pick_port(host: str, preferred: int, *, max_tries: int = 30) -> int:
    import socket

    for offset in range(max_tries):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise SystemExit(
        f"No free port near {preferred} (tried {max_tries} ports). "
        f"Stop the other process or run: python aio_serenity.py --port 3000"
    )
