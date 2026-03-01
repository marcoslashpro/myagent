from pathlib import Path

from ollama import chat

from prompt_toolkit import PromptSession
from rich.console import Console

from myagent.v1.errors import ModelResponseError
from myagent.v1.agent import Agent
from myagent.v1.models import Mount
from myagent.v1.environment.config import DockerSpecs, DockerConfig
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


if __name__ == "__main__":
    model_name = "ministral-3:8b"
    ctx = DockerConfig(
        mounts=[Mount(Path("~/.artifacts"), mode="rw")],
        specs=DockerSpecs(
            remote_repo="ghcr.io/astral-sh/uv:python3.14-alpine",
        ),
    )

    session = PromptSession()
    console = Console()

    with Agent(OllamaLLM(model_name), ctx) as ollama_agent:
        console.print(
            f"[INFO] - Success. Press Ctrl + C to quit at any time. Type any prompt to start."
        )

        while True:
            prompt = session.prompt(">>> ")
            ollama_agent.run(prompt)
