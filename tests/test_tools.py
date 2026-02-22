from myagent.v1.tools import tool, Tool

import pytest


def test_tool_wrapper():
    @tool
    def test_func():
        """Some docstring"""
        return 1

    assert isinstance(test_func, Tool)
    assert test_func.name == "test_func"
    assert test_func.description == "Some docstring"
