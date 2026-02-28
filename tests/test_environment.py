from collections.abc import Callable, Iterator
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Self
from unittest.mock import patch

from myagent.v1.actions import Observation
from myagent.v1.environment import Docker, _format_volumes_for_sys_prompt
import pytest

from myagent.v1.models import DockerSpecs, Mount, Volumes
from myagent.v1.tools import Tool


@pytest.mark.parametrize(
    "code", ["python3 -c 'print(\"Hello World\")'", 'echo "Hello World"']
)
def test_run_in_container(code):
    env = Docker([], [])
    env.start()
    out = env.run(code)
    env.stop()
    assert out == Observation(
        content="Hello World\n", type="observation", status_code=0
    )


def test_run_in_container_with_external_dockerfile():
    env = Docker([], [], specs=DockerSpecs(remote_repo="alpine"))
    env.start()
    out = env.run('echo "Hello World"')
    env.stop()
    assert out == Observation(
        content="Hello World\n", type="observation", status_code=0
    )


@pytest.mark.parametrize(
    "mnts, exp",
    [
        [
            [Mount(Path("somewhere"), "rw")],
            {
                "somewhere": {"bind": f"{Docker._mnt_dir}/somewhere", "mode": "rw"},
                str(Docker._artifacts_path): {
                    "bind": f"{Docker._mnt_dir}/{Docker._artifacts_path.name}",
                    "mode": "rw",
                },
            },
        ],
        [
            [Mount(Path("somewhere"), "ro")],
            {
                "somewhere": {"bind": f"{Docker._mnt_dir}/somewhere", "mode": "ro"},
                str(Docker._artifacts_path): {
                    "bind": f"{Docker._mnt_dir}/{Docker._artifacts_path.name}",
                    "mode": "rw",
                },
            },
        ],
    ],
)
def test_bind_mnts(mnts: list[Mount], exp: dict):
    with patch("myagent.v1.environment.Path.exists", return_value=True):
        env = Docker([], mnts)

    assert env._volumes == exp


@pytest.mark.parametrize(
    "volumes, exp",
    [
        [
            Volumes(
                {"somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "ro"}}
            ),
            f"|-{Docker._mnt_dir}/somepath  # ro\n",
        ],
        [
            Volumes(
                {"somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "rw"}}
            ),
            f"|-{Docker._mnt_dir}/somepath  # rw\n",
        ],
    ],
)
def test_format_volumes_for_sys_prompt(volumes, exp):
    assert _format_volumes_for_sys_prompt(volumes) == exp


@pytest.mark.parametrize(
    "volumes, subfiles, innerdirs, exp",
    [
        [
            Volumes(
                {"somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "ro"}}
            ),
            ["somefile"],
            [],
            f"|-{Docker._mnt_dir}/somepath/  # ro\n   |-somefile  # ro\n",
        ],
        [
            Volumes(
                {"somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "rw"}}
            ),
            ["somefile", "someother"],
            [],
            f"|-{Docker._mnt_dir}/somepath/  # rw\n   |-somefile  # rw\n   |-someother  # rw\n",
        ],
        [
            Volumes(
                {"somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "rw"}}
            ),
            ["somefile", "someother"],
            ["innerdir"],
            (
                f"|-{Docker._mnt_dir}/somepath/  # rw\n"
                f"   |-somefile  # rw\n"
                f"   |-someother  # rw\n"
                f"   |-innerdir/  # rw\n"
                f"      |-somefile  # rw\n"
                f"      |-someother  # rw\n"
            ),
        ],
        [
            Volumes(
                {
                    "somepath": {"bind": f"{Docker._mnt_dir}/somepath", "mode": "rw"},
                    "somefile": {"bind": f"{Docker._mnt_dir}/somefile", "mode": "rw"},
                }
            ),
            ["somefile", "someother"],
            ["innerdir"],
            (
                f"|-{Docker._mnt_dir}/somepath/  # rw\n"
                f"   |-somefile  # rw\n"
                f"   |-someother  # rw\n"
                f"   |-innerdir/  # rw\n"
                f"      |-somefile  # rw\n"
                f"      |-someother  # rw\n"
                f"|-{Docker._mnt_dir}/somefile  # rw\n"
            ),
        ],
    ],
)
def test_format_volumes_for_sys_prompt_with_dirs(volumes, subfiles, innerdirs, exp):
    more_than_once = False

    class MockPath(Path):
        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            return self.name == "somepath" or self.name == "innerdir"

        def walk(
            self,
            top_down: bool = True,
            on_error: Callable[[OSError], object] | None = None,
            follow_symlinks: bool = False,
        ) -> Iterator[tuple[Self, list[str], list[str]]]:
            nonlocal more_than_once
            if not more_than_once:
                more_than_once = True
                yield self, innerdirs, subfiles
            else:
                yield self, [], subfiles

    with patch("myagent.v1.environment.Path", new=MockPath):
        assert _format_volumes_for_sys_prompt(volumes) == exp
