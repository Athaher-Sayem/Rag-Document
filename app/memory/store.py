"""Per-session conversation memory.

In-process store keyed by session_id. Keeps a rolling window of recent turns
so long conversations stay focused. Swap for RedisChatMessageHistory /
Postgres-backed storage for multi-process deploys.
"""
from __future__ import annotations

from collections import defaultdict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.config import get_settings

_sessions: dict[str, list[BaseMessage]] = defaultdict(list)


def _window() -> int:
    return get_settings().memory_window * 2  # window of turns -> messages


def get_history(session_id: str) -> list[BaseMessage]:
    """Return the recent message window for a session (newest kept)."""
    return list(_sessions[session_id][-_window():])


def add_turn(session_id: str, user_message: str, ai_message: str) -> None:
    """Append a user/assistant pair to the session history."""
    history = _sessions[session_id]
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=ai_message))
    # Trim in place so memory does not grow unbounded.
    if len(history) > _window():
        del history[: len(history) - _window()]


def get_history_dicts(session_id: str) -> list[dict[str, str]]:
    """Serialize a session's history to role/content dicts for the API."""
    msgs = _sessions.get(session_id, [])
    return [
        {
            "role": "user" if isinstance(m, HumanMessage) else "assistant",
            "content": m.content if isinstance(m.content, str) else str(m.content),
        }
        for m in msgs
    ]


def clear_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
