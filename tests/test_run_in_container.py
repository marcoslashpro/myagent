from myagent.v1.environment import Docker
import pytest


@pytest.mark.parametrize('code', [
    "python3 -c 'print(\"Hello World\")'",
    "echo \"Hello World\""
])
def test_run_in_container(code):
    out = Docker('', []).run(code)
    assert out == "Hello World\n"