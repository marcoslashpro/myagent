from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Literal

import docker
import docker.errors

from myagent.core.log_config import AgentLogger
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


@dataclass(slots=True)
class Context:
    tools: list[Tool] = field(default_factory=list)
    mounts: list[str] = field(default_factory=list)


class Agent:
    _sys_prompt_path = Path(__file__).parent.parent / "prompts/docker_agent_sys.txt"

    def __init__(self, llm: LLM, ctx: Context | None = None, cli: bool = True):
        self.ctx = ctx
        self._messages: list[Message] = [self._generate_sys_prompt()]
        self.llm = llm
        if cli:
            from myagent.core.log_config import AgentLogger

            self.logger = AgentLogger()
        else:
            self.logger = None

    def log(
        self,
        type: Literal["final_answer", "code", "prompt", "env", "think", "exc"],
        msg: str,
    ):
        if not self.logger:
            return
        if type == "code":
            self.logger.log_code(msg)
        elif type == "env":
            self.logger.log_observation(msg)
        elif type == "final_answer":
            self.logger.log_final_answer(msg)
        elif type == "think":
            self.logger.log_think(msg)
        elif type == "prompt":
            self.logger.log_prompt(msg)
        elif type == "exc":
            self.logger.log_exeption(msg)

    @classmethod
    def _generate_sys_prompt(cls):
        return SystemMessage(content=cls._sys_prompt_path.read_text())

    def run(self, prompt: str):
        self._messages.append(UserMessage(content=prompt))
        self.log("prompt", prompt)

        while True:
            res = self.llm.run(self._messages)

            output = extract_all_blocks(res.content)

            match output:
                case AssistantOutput(think=None, code=None, final_answer=None):
                    self._messages.append(
                        UserMessage(
                            content="Invalid response content, make sure to wrap your answer is the specific block that it belongs to"
                        )
                    )
                    self.log("exc", f"Invalid response from agent: {output}")
                    continue
                case AssistantOutput(think=think, code=code, final_answer=final_answer):
                    if final_answer:
                        self._messages.append(AssistantMessage(content=final_answer))
                        self.log("final_answer", final_answer)
                        return
                    if think:
                        self.log("think", think)
                        self._messages.append(AssistantMessage(content=think))
                    if code:
                        self.log("code", code)
                        self._messages.append(AssistantMessage(code))

                        observation = run_in_container(code)
                        self.log("env", observation)

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
    try:
        output = client.containers.run(
            "python:3.12-slim",
            command=["sh", "-c", code],
            auto_remove=True,
            stdout=True,
            stderr=True,
        )
    except docker.errors.APIError as e:
        return e.explanation if e.explanation else str(e)
    except docker.errors.ContainerError as e:
        return str(e)

    return output.decode()
