from myagent.llm import LLM
from myagent.messages import Message, AssistantMessage, UserMessage 



class Agent[CtxT]:
    def __init__(self, llm: LLM, ctx: CtxT | None = None):
        self.ctx = ctx
        self._messages: list[Message] = []
        self.llm = llm

    def run(self, prompt: str) -> AssistantMessage:
        self._messages.append(UserMessage(content=prompt))
        return self.llm.run(self._messages)
