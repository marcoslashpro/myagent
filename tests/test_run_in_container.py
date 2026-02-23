from myagent.v1.agent import run_in_container
import pytest


@pytest.mark.parametrize('code', [
    "python3 -c 'print(\"Hello World\")'",
    "echo \"Hello World\""
])
def test_run_in_container(code):
    out = run_in_container(code)
    assert out == "Hello World\n"