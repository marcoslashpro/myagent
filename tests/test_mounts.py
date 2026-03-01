from pathlib import Path
from unittest.mock import patch

import pytest

from myagent.v1.environment._mounts import Mount, UserTool, AgentTool


@pytest.mark.parametrize(
    "mnt_dir, path, mode, exp",
    [
        [
            "/mnt",
            Path("somewhere"),
            "rw",
            {
                "somewhere": {"bind": f"/mnt/somewhere", "mode": "rw"},
            },
        ],
        [
            "/mnt",
            Path("somewhere"),
            "ro",
            {
                "somewhere": {"bind": f"/mnt/somewhere", "mode": "ro"},
            },
        ],
    ],
)
def test_mnts_to_volumes(mnt_dir, path, mode, exp: dict):
    with patch("myagent.v1.environment._mounts.Path.exists", return_value=True):
        assert Mount(path, mode).to_volumes(mnt_dir) == exp


@pytest.mark.parametrize(
    "mnt_dir, cls, path, exp",
    [
        (
            "/mnt/tools",
            UserTool,
            Path("somewhere"),
            {"somewhere": {"bind": "/mnt/tools/user/somewhere", "mode": "ro"}},
        ),
        (
            "/mnt/tools",
            AgentTool,
            Path("somewhere"),
            {"somewhere": {"bind": "/mnt/tools/agent/somewhere", "mode": "rw"}},
        ),
    ],
)
def test_tools_to_volumes(mnt_dir, cls, path, exp: dict):
    with patch("myagent.v1.environment._mounts.Path.exists", return_value=True), \
        patch("myagent.v1.environment._mounts.Path.is_dir", return_value=True):
        assert cls(path).to_volumes(mnt_dir) == exp
