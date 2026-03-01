import io
from pathlib import Path

from docker import DockerClient

from myagent.v1.environment._config import DockerConfig, DockerSpecs
from myagent.v1.errors import (
    DockerSetupError,
    InvalidDockerFileError,
    InvalidDockerSpecsError,
    InvalidMountError,
)
from myagent.v1.environment._models import AllVolumes, Volumes, RoOrRw
from myagent.v1.environment._mounts import UserTool, AgentTool, Mount

from docker.models.images import Image


def build_volumes(config: DockerConfig) -> AllVolumes:
    return AllVolumes(
        user_tools=build_tools_volumes(config.tools, config.mnt_tools_dir),
        agent_tools=build_agent_tools_volumes(
            config.LOCAL_AGENT_TOOLS_DIR, config.mnt_tools_dir
        ),
        docs=build_mnt_volumes(config.mnt_dir, config.mounts),
    )


def build_tools_volumes(tools: list[Tool], mnt_tools_dir: str) -> Volumes:
    volumes: Volumes = {}

    for tool in tools:
        volumes.update(
            _build_volume(
                str(tool.path),
                f"{mnt_tools_dir}/{tool.path.name}",
                tool.mode,
            )
        )

    return volumes


def build_agent_tools_volumes(
    local_agent_tools_dir: Path, mnt_tools_dir: str
) -> "Volumes":
    local_agent_tools_dir.mkdir(exist_ok=True)
    volumes: Volumes = {}

    for agent_tool in local_agent_tools_dir.iterdir():
        volumes.update(
            _build_volume(
                str(agent_tool),
                f"{mnt_tools_dir}/{agent_tool.name}",
                "rw",
            )
        )
    return volumes


def build_mnt_volumes(mnt_dir: str, mounts: list[Mount]) -> Volumes:
    volumes: Volumes = {}

    for mount in mounts:
        if not mount.path.expanduser().exists():
            raise InvalidMountError(path=str(mount.path))
        volumes.update(
            _build_volume(
                str(mount.path.expanduser()),
                f"{mnt_dir}/{mount.path.name}",
                mount.mode,
            )
        )
    return volumes


def build_img(client: DockerClient, specs: DockerSpecs | None) -> Image:
    _img_tag = specs.img_tag if specs else "agent-env:latest"

    if not specs or not specs.local_dockerfile or not specs.remote_repo:
        return client.images.build(
            fileobj=_build_default_dockerfile(),
            tag=_img_tag,
            forcerm=True,
        )[0]

    if specs.remote_repo and specs.local_dockerfile:
        raise DockerSetupError(
            "Cannot create a valid image when provided both "
            "dockerfile and an image to pull from registry. "
            "Please provide only one of the two."
        )

    if specs.local_dockerfile:
        if not specs.local_dockerfile.exists():
            raise InvalidDockerFileError(str(specs.local_dockerfile))

        return client.images.build(
            path=str(specs.local_dockerfile.parent.resolve()),
            dockerfile=specs.local_dockerfile.name,
            tag=_img_tag,
            forcerm=True,
        )[0]

    if specs.remote_repo:
        return client.images.pull(specs.remote_repo)

    else:
        raise InvalidDockerSpecsError(f"Invalid specs for docker container: {specs}")


def _build_volume(_from: str, to: str, mode: RoOrRw) -> Volumes:
    return {_from: {"bind": to, "mode": mode}}


def _build_default_dockerfile():
    return io.BytesIO(
        """
FROM python:3.12-slim
LABEL agent.shell='bash'
LABEL agent.description="Bash environment with python pre-installed"
LABEL agent.base_img='python:3.12-slim'
""".encode()
    )
