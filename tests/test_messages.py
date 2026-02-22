from dataclasses import asdict

from myagent.v1.messages import (
    ToolCall,
    ToolMessage,
    from_messages_to_dict,
    UserMessage,
    SystemMessage,
    AssistantMessage,
)

import pytest


@pytest.mark.parametrize(
    "msgs, exp",
    [
        ([UserMessage(content="foo")], [{"role": "user", "content": "foo"}]),
        (
            [AssistantMessage(content="foo")],
            [{"role": "assistant", "content": "foo", "tool_calls": None}],
        ),
        ([SystemMessage(content="foo")], [{"role": "system", "content": "foo"}]),
        (
            [SystemMessage(content="foo"), UserMessage(content="bar")],
            [{"role": "system", "content": "foo"}, {"role": "user", "content": "bar"}],
        ),
        (
            [ToolMessage(content="foo", name="bar")],
            [{"role": "tool", "content": "foo", "name": "bar"}],
        ),
    ],
)
def test_convert_messages_to_dict(msgs, exp):
    converted = from_messages_to_dict(msgs)
    assert all([msg == e for msg, e in zip(converted, exp)])


@pytest.mark.parametrize(
    "msgs, exp",
    [
        (
            [
                AssistantMessage(
                    content=None,
                    tool_calls=[
                        ToolCall(args={"foo": "bar"}, name="some tool")
                    ],
                )
            ],
            [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {"id": "test", "args": {"foo": "bar"}, "name": "some tool"}
                    ],
                }
            ],
        ),
    ],
)
def test_convert_assistant_messages_with_tool_calls(msgs, exp):
    converted = from_messages_to_dict(msgs)
    for expected_msg, dict_msg in zip(exp, converted, strict=True):
        assert all(
            [
                exp_tool_call == actual_tool_call
                for exp_tool_call, actual_tool_call in zip(
                    expected_msg["tool_calls"], dict_msg["tool_calls"]
                )
            ]
        )
