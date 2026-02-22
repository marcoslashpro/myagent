from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class UserMessage:
    content: str
    role: Literal["user"] = "user"


@dataclass(slots=True)
class AssistantMessage:
    content: str
    role: Literal["assistant"] = "assistant"


@dataclass(slots=True)
class SystemMessage:
    content: str
    role: Literal["system"] = "system"


def from_messages_to_dict(messages: list[Message]) -> list[dict]:
    return [asdict(m) for m in messages]

Message = SystemMessage | AssistantMessage | UserMessage 