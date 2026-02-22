from dataclasses import dataclass, field
import re

import docker

from myagent.v1.actions import AssistantOutput
from myagent.v1.errors import ModelError, ToolError
from myagent.v1.llm import LLM
from myagent.v1.messages import (
    AssistantMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from myagent.core.messages import Message, SystemMessage
from myagent.v1.tools import Tool

from rich.console import Console
from rich.markdown import Markdown


console = Console()


@dataclass(slots=True)
class Context:
    system_prompt: str = field(default_factory=str)
    tools: list[Tool] = field(default_factory=list)
    mounts: list[str] = field(default_factory=list)


class Agent:
    def __init__(self, llm: LLM, ctx: Context | None = None):
        self.ctx = ctx
        self._messages: list[Message] = (
            [SystemMessage(content=ctx.system_prompt)] if ctx else []
        )
        self.llm = llm

    def run(self, prompt: str):
        self._messages.append(UserMessage(content=prompt))

        while True:
            console.log(
                "[DEBUG] - Calling model with messages:\n"
                f"{"\n\n".join([str(msg) for msg in self._messages])}"
            )
            res = self.llm.run(self._messages)

            console.log(f"[DEBUG] - Extracting blocks from: {res.content}")
            output = extract_all_blocks(res.content)

            console.log(Markdown(f"[DEBUG] - **Extracted blocks**: {output}\n\n"))

            match output:
                case AssistantOutput(think=None, code=None, final_answer=None):
                    self._messages.append(
                        UserMessage(
                            content="Invalid response content, please remember to wrap your answer is the specific block that it belongs to"
                        )
                    )
                    continue
                case AssistantOutput(think=think, code=code, final_answer=final_answer):
                    if final_answer:
                        self._messages.append(AssistantMessage(content=final_answer))
                        return
                    if think:
                        self._messages.append(AssistantMessage(content=think))
                    if code:
                        self._messages.append(AssistantMessage(code))

                        observation = run_in_container(code)
                        console.log(f"Generated observtion: {observation}")

                        self._messages.append(UserMessage(content=observation))

    @staticmethod
    def _create_tool_mapping(tools: list[Tool]) -> dict[str, Tool]:
        return {tool.name: tool for tool in tools}

    @staticmethod
    def _execute_tool_calls(
        tools: dict[str, Tool], tool_calls: list[ToolCall]
    ) -> list[ToolMessage]:
        results: list[ToolMessage] = []

        for tool_call in tool_calls:
            to_exec = tools.get(tool_call.name)

            if not to_exec:
                raise ModelError(
                    f"Tool with name: {tool_call.name} does not exist",
                )

            try:
                tool_res = to_exec.func(**tool_call.args)
                results.append(ToolMessage(content=str(tool_res), name=to_exec.name))
            except TypeError as e:
                raise ToolError(str(e), to_exec.name) from e

        return results


def extract_all_blocks(prompt: str) -> AssistantOutput:
    actions = ["think", "code", "final_answer"]
    # 1. Join labels into an OR group: (think|code|final)
    actions_regex = "|".join(actions)

    # 2. Pattern: Matches backticks, then one of the labels, then the content
    # We use a non-greedy match (.*?) to stop at the NEXT closing backticks
    pattern = rf"```({actions_regex})\n([\s\S]*?)```"

    results = {}

    # 3. Use finditer to loop through every occurrence
    for match in re.finditer(pattern, prompt):
        label = match.group(1)  # The action name
        content = match.group(2).strip()  # The actual block content
        results[label] = content

    return AssistantOutput(**results)


def run_in_container(code: str) -> str:
    client = docker.from_env()
    output = client.containers.run(
        "python:3.12-slim",
        command=code.split(),
        auto_remove=True,
        stdout=True,
        stderr=True,
    )
    return f"```observation\n{output.decode()}\n```"
