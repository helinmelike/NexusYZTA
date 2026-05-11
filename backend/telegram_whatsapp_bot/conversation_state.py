from __future__ import annotations


_USER_SESSIONS: dict[int, dict[str, object]] = {}


def get_user_session(user_id: int) -> dict[str, object]:
    return _USER_SESSIONS.setdefault(user_id, {})


def get_state(user_id: int) -> str | None:
    session = get_user_session(user_id)
    state = session.get("state")
    return str(state) if state else None


def set_state(user_id: int, state: str, **payload: object) -> None:
    session = get_user_session(user_id)
    session["state"] = state
    for key, value in payload.items():
        session[key] = value


def clear_state(user_id: int) -> None:
    session = get_user_session(user_id)
    session.pop("state", None)
    session.pop("pending_order", None)
    session.pop("product_candidates", None)
    session.pop("pending_quantity", None)


def has_active_state(user_id: int) -> bool:
    return get_state(user_id) is not None
