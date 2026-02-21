from dataclasses import asdict, dataclass
from typing import Literal


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


Message = SystemMessage | AssistantMessage | UserMessage


def from_messages_to_dict(messages: list[Message]) -> list[dict]:
    return [asdict(m) for m in messages]
