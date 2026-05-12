from __future__ import annotations


class AIContextStore:
    def __init__(self) -> None:
        self._store: dict[int, dict[str, object]] = {}

    def get(self, user_id: int) -> dict[str, object]:
        return self._store.setdefault(user_id, {})

    def clear(self, user_id: int) -> None:
        self._store.pop(user_id, None)

    def set_pending(self, user_id: int, action: str, payload: dict[str, object] | None = None) -> None:
        ctx = self.get(user_id)
        ctx["pending_action"] = action
        ctx["pending_payload"] = payload or {}

    def pop_pending(self, user_id: int) -> tuple[str | None, dict[str, object]]:
        ctx = self.get(user_id)
        action = ctx.pop("pending_action", None)
        payload = ctx.pop("pending_payload", {})
        return action, payload if isinstance(payload, dict) else {}


ai_context_store = AIContextStore()
