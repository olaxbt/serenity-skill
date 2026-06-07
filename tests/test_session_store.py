"""Session store tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin import session_store


def test_session_create_and_message(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "DB_PATH", tmp_path / "test_sessions.db")
    session_store.init_db()
    s = session_store.create_session("Test")
    session_store.save_message(
        s["id"],
        prompt="What about $SIVE?",
        mode="A",
        ticker="SIVE",
        html_snapshot="<div>ok</div>",
        structured={"sections": []},
        markdown="md",
        llm_narrative="narr",
    )
    msgs = session_store.get_session_messages(s["id"])
    assert len(msgs) == 1
    assert msgs[0]["ticker"] == "SIVE"
    sessions = session_store.list_sessions()
    assert sessions[0]["title"].startswith("What about")
