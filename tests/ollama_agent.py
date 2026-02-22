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

        print(
            f"[DEBUG] - Calling model with messages: {"\n\n".join([str(msg) for msg in messages_dict])}\n"
        )

        res = chat(
            messages=messages_dict,
            model=model or self.model,
        )

        if not (content := res.message.content):
            raise ModelResponseError("Missing content from the response")

        print(f"[DEBUG] - Model Response: {content}\n")
        return AssistantMessage(content=content)


ctx = Context(
    system_prompt=(
        Path(__file__).parent / "assets/docker_agent_sys_prompt.txt"
    ).read_text()
)


ollama_agent = Agent(OllamaLLM("ministral-3:8b"), ctx)
print(ollama_agent.run("How you doing?"), end="\n\n")
