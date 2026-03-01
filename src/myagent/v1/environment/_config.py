from dataclasses import dataclass, field
from pathlib import Path

from myagent.v1.errors import DockerConfigError
from myagent.v1.environment._mounts import Tool, Mount, UserTool


_ROOT_DIR_NAME = "~/.myagent"
_LOCAL_AGENT_TOOLS_DIR = "tools"
_SYS_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts/docker_agent_sys.txt"


@dataclass(slots=True)
class DockerSpecs:
    local_dockerfile: Path | None = field(default=None)
    remote_repo: str | None = field(default=None)
    img_tag: str = field(default="agent-env:latest")


@dataclass(slots=True)
class DockerConfig:
    specs: DockerSpecs | None = field(default=None)
    mnt_dir: str = field(default="/mnt")
    mnt_tools_dir: str = field(default="/mnt/tools")
    tools: list[UserTool] = field(default_factory=list)
    mounts: list[Mount] = field(default_factory=list)

    @property
    def LOCAL_ROOT_DIR(self) -> Path:
        if not (_root_path := Path(_ROOT_DIR_NAME).expanduser()).exists():
            _root_path.mkdir(exist_ok=True)

        return _root_path

    @property
    def LOCAL_AGENT_TOOLS_DIR(self) -> Path:
        if not (
            _tools_path := self.LOCAL_ROOT_DIR.joinpath(_LOCAL_AGENT_TOOLS_DIR)
        ).exists():
            _tools_path.mkdir(exist_ok=True)

        return _tools_path

    @property
    def SYS_PROMPT_PATH(self) -> Path:
        if not (_sys_prompt_path := Path(_SYS_PROMPT_PATH)).exists():
            raise DockerConfigError(
                f"[FATAL ERROR] - Unable to locate system prompt at path: {_sys_prompt_path}, "
                "please inform the library maintainers."
            )
        return _sys_prompt_path
