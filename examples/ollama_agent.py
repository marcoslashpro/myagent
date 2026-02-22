from pathlib import Path

from ollama import chat
from rich.console import Console
from rich.markdown import Markdown

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


if __name__ == "__main__":
    model_name = "ministral-3:8b"

    console = Console()

    console.print(f"[INFO] - Initializing {model_name}")
    ollama_agent = Agent(OllamaLLM(model_name))

    console.print(f"[INFO] - Success. Press Ctrl + C to quit at any time.")

    while True:
        console.print(Markdown("**You**"))
        ollama_agent.run(input("- "))
