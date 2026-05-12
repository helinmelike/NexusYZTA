from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IntentType(str, Enum):
    LIST_PRODUCTS = "LIST_PRODUCTS"
    CREATE_ORDER = "CREATE_ORDER"
    TRACK_CARGO = "TRACK_CARGO"
    CANCEL_ORDER = "CANCEL_ORDER"
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"


@dataclass
class ParsedIntent:
    intent: IntentType
    entities: dict[str, object] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""


@dataclass
class RouteResult:
    handled: bool
    response_text: str = ""
