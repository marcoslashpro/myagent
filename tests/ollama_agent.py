from ollama import chat

from myagent.errors import ModelError
from myagent.main import Agent, Message, AssistantMessage
from myagent.messages import from_messages_to_dict


class OllamaLLM:
    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, messages: list[Message], model: str | None = None) -> AssistantMessage:
        res = chat(
            messages=from_messages_to_dict(messages),
            model=model or self.model
        )
        
        if not (content := res.message.content):
            raise ModelError("Missing response content")
        
        return AssistantMessage(content=content)
    

ollama_agent = Agent(OllamaLLM('qwen3:4b'))
print(ollama_agent.run("How you doing?").content)
