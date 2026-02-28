from typing import Literal
import re

from myagent.core.messages import Message, SystemMessage
from myagent.v1.actions import AgentAction
from myagent.v1.environment import Docker, DockerConfiguration
from myagent.v1.errors import AgentEnvironmentError, UserError
from myagent.v1.llm import LLM
from myagent.v1.messages import AssistantMessage, UserMessage


class Agent:
    def __init__(
        self,
        llm: LLM,
        config: DockerConfiguration | None = None,
        messages: list[Message] | None = None,
        cli: bool = True,
    ):
        self.config = config if config else DockerConfiguration()
        self.env = Docker.from_config(self.config)
        self.system_prompt = self._generate_sys_prompt()

        self.messages = messages or [self._generate_sys_prompt()]

        self.llm = llm
        if cli:
            from myagent.core.log_config import AgentLogger

            self.logger = AgentLogger()
        else:
            self.logger = None

    def _generate_sys_prompt(self) -> SystemMessage:
        sys_prompt = self.config.SYS_PROMPT_PATH.read_text()
        sys_prompt = (
            sys_prompt.replace("{{IMAGE_METADATA}}", str(self.env.img_metadata))
            .replace("{{SHELL}}", self.env.img_metadata.shell)
            .replace("{{FILES}}", self.env.volumes.render_for_sys_prompt())
            .replace("{{MNT_DIR}}", self.config.mnt_dir)
            .replace("{{TOOL_DIR}}", self.config.mnt_tools_dir)
        )
        return SystemMessage(content=sys_prompt)

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

    def __enter__(self):
        print("\n[INFO] - Starting container...")
        self.env.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        print("\n[INFO] - Stopping container...")
        self.env.stop()

    def run(self, prompt: str):
        self.messages.append(UserMessage(content=prompt))
        self.log("prompt", prompt)

        while True:
            res = self.llm.run(self.messages)

            output = extract_all_blocks(res.content)

            if not output.code and not output.think and not output.final_answer:
                self.messages.append(
                    UserMessage(
                        content="Invalid response content, make sure to wrap your answer is the specific block that it belongs to"
                    )
                )
                self.log("exc", f"Invalid response from agent: {res.content}")
                continue

            if think := output.think:
                self.log("think", think)
                self.messages.append(AssistantMessage(content=think))

            if code := output.code:
                self.log("code", code)
                self.messages.append(AssistantMessage(code))

                try:
                    observation = self.env.run(code)
                except AgentEnvironmentError as e:
                    raise UserError(
                        "Agent environment not properly initialized, please make sure to "
                        "use the agent in a `with` block."
                    )

                self.log("env", str(observation))

                self.messages.append(UserMessage(content=str(observation)))

            if final_answer := output.final_answer:
                self.log("final_answer", final_answer)
                self.messages.append(AssistantMessage(content=final_answer))
                return


def extract_all_blocks(prompt: str) -> AgentAction:
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

    return AgentAction(**results)


if __name__ == "__main__":
    from rich import print, markdown as md

    print(md.Markdown(Agent(None, DockerConfiguration()).messages[0].content))  # type: ignore
