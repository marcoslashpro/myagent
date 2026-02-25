from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from myagent.v1.errors import InvalidToolMountError
from myagent.v1.tools import tool, Tool, validate_tool

import pytest


def test_tool_wrapper():
    @tool
    def test_func():
        """Some docstring"""
        return 1

    assert isinstance(test_func, Tool)
    assert test_func.name == "test_func"
    assert test_func.description == "Some docstring"


def test_validate_tools_raises_missing_launch_file():
    with TemporaryDirectory() as temp_dir:
        Path(temp_dir).joinpath("README.md").write_text("")

        with pytest.raises(InvalidToolMountError):
            validate_tool(Path(temp_dir))


def test_validate_tool_raises_when_tool_is_not_dir():
    with NamedTemporaryFile() as temp_f:
        with pytest.raises(InvalidToolMountError):
            validate_tool(Path(temp_f.name))
