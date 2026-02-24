from unittest.mock import patch

from myagent.core.messages import AssistantMessage, UserMessage
from myagent.v1.actions import AgentAction
from myagent.v1.agent import Agent, extract_all_blocks
from myagent.v1.errors import ModelError, ToolError
from myagent.v1.messages import ToolCall
from myagent.v1.tools import Tool

import pytest


@pytest.mark.parametrize(
    "tools", [[Tool(lambda: 1, name="test", description="nothing really")], []]
)
def test_create_tool_mapping(tools: list[Tool]):
    out = Agent._create_tool_mapping(tools)
    tool_names = [tool.name for tool in tools]
    dict_keys = list(out.keys())
    assert all(
        [tool_name == dict_key] for tool_name, dict_key in zip(tool_names, dict_keys)
    )


@pytest.mark.parametrize(
    "tools_dict, tool_calls",
    [({"foo": Tool(lambda: 1, name="foo", description="bar")}, [ToolCall({}, "foo")])],
)
def test_execute_tool_calls(tools_dict, tool_calls):
    res = Agent._execute_tool_calls(tools_dict, tool_calls)

    assert len(res) == len(tool_calls)

    for r, tool_call in zip(res, tool_calls):
        assert r.name == tool_call.name


def test_execute_tool_call_with_invalid_name():
    with pytest.raises(ModelError):
        Agent._execute_tool_calls(
            {"foo": Tool(lambda: 1, "foo")}, tool_calls=[ToolCall(name="bar", args={})]
        )


def test_execute_tool_call_with_invalid_args():
    with pytest.raises(ToolError):
        Agent._execute_tool_calls(
            {"foo": Tool(lambda x: 1, "foo")},
            tool_calls=[ToolCall(name="foo", args={})],
        )


@pytest.mark.parametrize(
    "text, exp",
    [
        ("```think\nSomething```", AgentAction(think="Something")),
        (
            "```think\nSomething``````code\nls``````final_answer\nDone```",
            AgentAction(final_answer="Done", think="Something", code="ls"),
        ),
        ("```bdafojb```", AgentAction()),
        ("``````", AgentAction()),
    ],
)
def test_extract_blocks(text, exp):
    extracted = extract_all_blocks(text)
    assert extracted == exp


@pytest.mark.parametrize(
    "msgs, exp",
    [
        (
            ["```code\nls```", "```final_answer\nDone```"],
            [
                UserMessage(content=""),
                AssistantMessage(content="ls"),
                UserMessage(content="Env:ls"),
                AssistantMessage(content="Done"),
            ],
        ),
        (
            ["```think\nThinking```", "```final_answer\nDone```"],
            [
                UserMessage(content=""),
                AssistantMessage(content="Thinking"),
                AssistantMessage(content="Done"),
            ],
        ),
        (
            ["```think\nThinking``````code\nls```````final_answer\nDone```"],
            [
                UserMessage(content=""),
                AssistantMessage(content="Thinking"),
                AssistantMessage(content="ls"),
                UserMessage(content="Env:ls"),
                AssistantMessage(content="Done"),
            ],
        ),
        (
            ["```think\nThinking``````code\nls```", "```final_answer\nDone```"],
            [
                UserMessage(content=""),
                AssistantMessage(content="Thinking"),
                AssistantMessage(content="ls"),
                UserMessage(content="Env:ls"),
                AssistantMessage(content="Done"),
            ],
        ),
        (
            ["```think\nThinking```", "```code\nls````", "```final_answer\nDone```"],
            [
                UserMessage(content=""),
                AssistantMessage(content="Thinking"),
                AssistantMessage(content="ls"),
                UserMessage(content="Env:ls"),
                AssistantMessage(content="Done"),
            ],
        ),
    ],
)
def test_run(msgs, exp):
    class LLM:
        def __init__(self, model: str):
            self.model = model
            self.msgs = iter(msgs)

        def _iter_msgs(self):
            try:
                return next(self.msgs)
            except StopIteration:
                pass

        def run(self, messages, model=None):
            return AssistantMessage(content=self._iter_msgs() or "")

    with patch("myagent.v1.agent.Docker.run", new=lambda self, x: f"Env:{x}"):
        agent = Agent(LLM(""), cli=False)
        agent.run("")

        # First message is the system prompt, beyond the scope of testing,
        # might make the system prompt injectable, but for this specific agent
        # We need a sophisticated sys prompt that I cannot expect the user to
        # insert, and if I put it in the __init__, then the user is "welcome"
        # to put his own, but he really is not.
        assert agent._messages[1:] == exp
