from dataclasses import asdict

from myagent.v1.messages import (
    ToolCall,
    ToolMessage,
    UserMessage,
    SystemMessage,
    AssistantMessage,
)
from myagent.core.messages import from_messages_to_dict

import pytest


@pytest.mark.parametrize(
    "msgs, exp",
    [
        ([UserMessage(content="foo")], [{"role": "user", "content": "foo"}]),
        (
            [AssistantMessage(content="foo")],
            [{"role": "assistant", "content": "foo"}],
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
