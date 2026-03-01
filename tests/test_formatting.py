from collections.abc import Callable
from pathlib import Path
from typing import Iterator, Self

import pytest

from myagent.v1.environment._models import Volumes
import myagent.v1.environment._formatter as formatter


@pytest.mark.parametrize(
    "volumes, exp",
    [
        [
            Volumes({"somepath": {"bind": f"/mnt/somepath", "mode": "ro"}}),
            f"|-/mnt/somepath  # ro\n",
        ],
        [
            Volumes({"somepath": {"bind": f"/mnt/somepath", "mode": "rw"}}),
            f"|-/mnt/somepath  # rw\n",
        ],
    ],
)
def test_format_volumes_for_sys_prompt(volumes, exp):
    assert formatter.format_docs_dir(volumes) == exp


@pytest.mark.parametrize(
    "volumes, subfiles, innerdirs, exp",
    [
        [
            Volumes({"somepath": {"bind": f"/mnt/somepath", "mode": "ro"}}),
            ["somefile"],
            [],
            f"|-/mnt/somepath/  # ro\n   |-somefile  # ro\n",
        ],
        [
            Volumes({"somepath": {"bind": f"/mnt/somepath", "mode": "rw"}}),
            ["somefile", "someother"],
            [],
            f"|-/mnt/somepath/  # rw\n   |-somefile  # rw\n   |-someother  # rw\n",
        ],
        [
            Volumes({"somepath": {"bind": f"/mnt/somepath", "mode": "rw"}}),
            ["somefile", "someother"],
            ["innerdir"],
            (
                f"|-/mnt/somepath  # rw\n"
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
                    "somepath": {"bind": f"/mnt/somepath", "mode": "rw"},
                    "somefile": {"bind": f"/mnt/somefile", "mode": "rw"},
                }
            ),
            ["somefile", "someother"],
            ["innerdir"],
            (
                f"|-/mnt/somepath  # rw\n"
                f"   |-somefile  # rw\n"
                f"   |-someother  # rw\n"
                f"   |-innerdir/  # rw\n"
                f"      |-somefile  # rw\n"
                f"      |-someother  # rw\n"
                f"|-/mnt/somefile  # rw\n"
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

    assert formatter.format_docs_dir(volumes) == exp
