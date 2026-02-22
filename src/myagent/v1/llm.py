from typing import Protocol

from myagent.core.messages import AssistantMessage, Message
from myagent.v1.tools import Tool


class LLM(Protocol):
    model: str

    def __init__(self, model: str) -> None:
        self.model = model

    def run(
        self, messages: list[Message], model: str | None = None
    ) -> AssistantMessage: ...
