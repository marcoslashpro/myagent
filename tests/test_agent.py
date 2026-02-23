from myagent.core.messages import AssistantMessage
from myagent.v1.actions import AssistantOutput
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
        ("```think\nSomething```", AssistantOutput(think="Something")),
        (
            "```think\nSomething``````code\nls``````final_answer\nDone```",
            AssistantOutput(final_answer="Done", think="Something", code="ls"),
        ),
        ('```bdafojb```', AssistantOutput()),
        ('``````', AssistantOutput())
    ],
)
def test_extract_blocks(text, exp):
    extracted = extract_all_blocks(text)
    assert extracted == exp
