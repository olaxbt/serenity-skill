"""SQLite session history for browser UI."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from serenity_twin.paths import DATA

DB_PATH = DATA / "sessions.db"
MAX_SESSIONS = 50


def _conn() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                mode TEXT,
                ticker TEXT,
                html_snapshot TEXT,
                structured_json TEXT,
                markdown TEXT,
                llm_narrative TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            """
        )


def create_session(title: str = "New chat") -> dict[str, str]:
    init_db()
    sid = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    title = (title or "New chat")[:120]
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (sid, title, now, now),
        )
    _trim_old_sessions()
    return {"id": sid, "title": title, "created_at": now}


def list_sessions(limit: int = MAX_SESSIONS) -> list[dict[str, Any]]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, prompt, mode, ticker, html_snapshot, structured_json, markdown, llm_narrative, created_at "
            "FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("structured_json"):
            try:
                d["structured"] = json.loads(d["structured_json"])
            except json.JSONDecodeError:
                pass
        out.append(d)
    return out


def save_message(
    session_id: str,
    *,
    prompt: str,
    mode: str | None,
    ticker: str | None,
    html_snapshot: str,
    structured: dict | None,
    markdown: str,
    llm_narrative: str = "",
) -> dict[str, str]:
    init_db()
    mid = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    struct_json = json.dumps(structured, ensure_ascii=False) if structured else None
    with _conn() as c:
        count = c.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)).fetchone()[0]
        if count == 0:
            c.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                ((prompt or "New chat")[:120], now, session_id),
            )
        else:
            c.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        c.execute(
            "INSERT INTO messages (id, session_id, prompt, mode, ticker, html_snapshot, structured_json, markdown, llm_narrative, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, session_id, prompt, mode, ticker, html_snapshot, struct_json, markdown, llm_narrative, now),
        )
    return {"id": mid, "created_at": now}


def _trim_old_sessions() -> None:
    with _conn() as c:
        ids = [
            r[0]
            for r in c.execute(
                "SELECT id FROM sessions ORDER BY updated_at DESC LIMIT -1 OFFSET ?",
                (MAX_SESSIONS,),
            ).fetchall()
        ]
        for sid in ids:
            c.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
            c.execute("DELETE FROM sessions WHERE id = ?", (sid,))
