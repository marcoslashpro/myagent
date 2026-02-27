from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from myagent.v1.errors import InvalidToolMountError
from myagent.v1.tools import AgentTool, UserTool

import pytest


tools = [UserTool, AgentTool]


@pytest.mark.parametrize("tool", tools)
def test_validate_tools_raises_missing_launch_file(tool):
    with TemporaryDirectory() as temp_dir:
        Path(temp_dir).joinpath("README.md").write_text("")

        with pytest.raises(InvalidToolMountError):
            tool(Path(temp_dir))


@pytest.mark.parametrize("tool", tools)
def test_validate_tool_raises_when_tool_is_not_dir(tool):
    with NamedTemporaryFile() as temp_f:
        with pytest.raises(InvalidToolMountError):
            tool(Path(temp_f.name))
