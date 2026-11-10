"""Protocol helpers for JSON newline-delimited message serialization."""

import json
from typing import Any, Dict


def serialize_message(message: Dict[str, Any]) -> bytes:
    """Encode dictionary payload into UTF-8 JSON line."""
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def parse_message(raw_bytes: bytes) -> Dict[str, Any]:
    """Parse UTF-8 JSON line into dictionary payload."""
    text = raw_bytes.decode("utf-8").strip()
    return json.loads(text)
