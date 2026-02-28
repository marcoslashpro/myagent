from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Self
from unittest.mock import patch

from myagent.v1.actions import Observation
from myagent.v1.environment import (
    Docker,
    DockerConfiguration,
)
import pytest

from myagent.v1.models import Mount, Volumes


@pytest.mark.parametrize(
    "code", ["python3 -c 'print(\"Hello World\")'", 'echo "Hello World"']
)
def test_run_in_container(code):
    env = Docker.from_config(DockerConfiguration())
    env.start()
    out = env.run(code)
    env.stop()
    assert out == Observation(
        content="Hello World\n", type="observation", status_code=0
    )


def test_run_in_container_with_external_dockerfile():
    env = Docker.from_config(DockerConfiguration())
    env.start()
    out = env.run('echo "Hello World"')
    env.stop()
    assert out == Observation(
        content="Hello World\n", type="observation", status_code=0
    )