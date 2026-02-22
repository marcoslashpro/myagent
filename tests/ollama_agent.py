from pathlib import Path

from ollama import chat

from myagent.v1.errors import ModelError, ModelResponseError
from myagent.v1.agent import Agent, Context
from myagent.core.messages import (
    Message,
    AssistantMessage,
    from_messages_to_dict,
)


class OllamaLLM:
    def __init__(self, model: str) -> None:
        self.model = model

    def run(
        self, messages: list[Message], model: str | None = None
    ) -> AssistantMessage:

        messages_dict = from_messages_to_dict(messages)

        res = chat(
            messages=messages_dict,
            model=model or self.model,
        )

        if not (content := res.message.content):
            raise ModelResponseError("Missing content from the response")

        return AssistantMessage(content=content)


ctx = Context(
    system_prompt=(
        Path(__file__).parent / "assets/docker_agent_sys_prompt.txt"
    ).read_text()
)


ollama_agent = Agent(OllamaLLM("ministral-3:8b"), ctx)
ollama_agent.run("What files are in your current dir?")
