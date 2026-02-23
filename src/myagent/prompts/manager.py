from pathlib import Path

from myagent.v1.models import Mount


SYS_PROMPT_PATH = Path(__file__).parent / "docker_agent_sys.txt"


def render_sys_prompt(mnt_dir: str, files: list[Mount]) -> str:
    formatted = ""
    sys_prompt = SYS_PROMPT_PATH.read_text()

    for mnt in files:
        if mnt.path.is_dir():
            for _, _, filenames in mnt.path.walk():
                for file in filenames:
                    formatted += (
                        f"File: {mnt_dir}/{mnt.path.name}/{file} - Permissions: {mnt.mode}\n"
                    )
        else:
            formatted += (
                f"File: {mnt_dir}/{mnt.path.name} - Permissions: {mnt.mode}\n"
            )
    return sys_prompt.replace(
        "{{FILES}}",
        formatted,
    )


if __name__ == "__main__":
    print(render_sys_prompt("mnt", [Mount(Path(__file__).parent, "ro")]))
