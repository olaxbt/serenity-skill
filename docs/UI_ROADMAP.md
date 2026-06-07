# UI roadmap — streaming, session history, mobile

> **Status:** v0.3.2 — agent plan UX, purple theme, OlaXBT community sidebar.

Priority built in order:

1. **Session history (SQLite)** — `corpus/data/sessions.db`, sidebar list, new chat  
2. **Streaming Phase A** — `/api/chat/stream` progress events → **agent plan step UI**  
3. **Streaming Phase B** — DeepSeek token stream into Agent analysis section  
4. **Mobile drawer** — hamburger sidebar, fixed composer, thesis modal, 44px targets  
5. **Cursor agent parity** — `agent_prompt.py` + same script chain + SKILL workflows for Mode C/D  
6. **Purple theme + OlaXBT links** — `#e781fd`, [`ui/links.json`](../ui/links.json)  

See [`serenity_twin/agent_prompt.py`](../serenity_twin/agent_prompt.py), [`serenity_twin/session_store.py`](../serenity_twin/session_store.py).

## Not yet implemented

- Export session as Markdown  
- PWA manifest / installable app  
- Cancel mid-stream server-side (client abort only)  
- Premium search API (Serper/Tavily)  

## Agent compliance E2E (Cursor) — spec only

Separate from browser UI. Would test that **Cursor Agent** (not this server) runs required scripts when user chats. Not built — see README FAQ.
