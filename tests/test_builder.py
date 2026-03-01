
from pathlib import Path
from unittest.mock import patch

import pytest

from myagent.v1.models import Mount
from myagent.v1.environment._builder import build_mnt_volumes

@pytest.mark.parametrize(
    "mnt_dir, mnts, exp",
    [
        [
            "/mnt",
            [Mount(Path("somewhere"), "rw")],
            {
                "somewhere": {"bind": f"/mnt/somewhere", "mode": "rw"},
            },
        ],
        [
            "/mnt",
            [Mount(Path("somewhere"), "ro")],
            {
                "somewhere": {"bind": f"/mnt/somewhere", "mode": "ro"},
            },
        ],
    ],
)
def test_bind_mnts(mnt_dir, mnts: list[Mount], exp: dict):
    with patch("myagent.v1.environment._builder.Path.exists", return_value=True):
        assert build_mnt_volumes(mnt_dir=mnt_dir, mounts=mnts) == exp
