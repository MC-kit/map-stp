from __future__ import annotations

from typing import Any

from eliot import MemoryLogger


class MemoryDestination(MemoryLogger):  # type: ignore[misc]
    """Eliot memory logger."""

    def __call__(self, message: dict[str, Any]) -> None:
        self.write(message)

    def check_message(self, key: str, msg: str) -> bool:
        """Check message in memory log."""
        return any(key in m and msg in m[key] for m in self.messages)
