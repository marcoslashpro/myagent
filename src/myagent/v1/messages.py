from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from myagent.core.messages import SystemMessage, UserMessage, AssistantMessage


@dataclass(slots=True)
class ToolCall:
    args: dict[str, Any]
    name: str


@dataclass(slots=True)
class ToolMessage:
    content: str
    name: str
    role: Literal["tool"] = "tool"


Message = SystemMessage | UserMessage | ToolMessage | AssistantMessage 
