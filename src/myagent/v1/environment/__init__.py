from docker import DockerClient
import docker.errors
from docker.models.containers import Container
from docker.models.images import Image

from myagent.v1.actions import Observation
from myagent.v1.environment.config import DockerConfiguration
from myagent.v1.errors import AgentEnvironmentError
from myagent.v1.models import AllVolumes, ImageMetadata

import myagent.v1.environment._builder as builder


class Docker:
    def __init__(
        self,
        img: Image,
        volumes: AllVolumes,
        client: DockerClient | None = None,
    ):
        self.img = img
        self.volumes = volumes
        self.client = client or DockerClient.from_env()

        self.img_metadata: ImageMetadata = ImageMetadata.from_img(img)
        self.container: Container | None = None

    @classmethod
    def from_config(cls, config: DockerConfiguration) -> "Docker":
        client = DockerClient.from_env()
        volumes = builder.build_volumes(config)
        img = builder.build_img(client, config.specs)
        return cls(img=img, volumes=volumes, client=client)

    def start(self):
        self._container = self.client.containers.run(
            self.img,
            command=f"{self.img_metadata.shell} -c 'while true; do sleep 1; done'",
            detach=True,
            tty=False,
            volumes=self.volumes.to_docker_volumes(),
            cap_drop=["ALL"],  # drop all linux capabilities
            tmpfs={"/tmp": "size=64m"},
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            cap_add=["NET_RAW"],  # add back only what's needed for networking
            security_opt=["no-new-privileges:true"],  # prevent privilege escalation
            pids_limit=100,  # prevent fork bombs
        )

    def run(self, cmd: str) -> Observation:
        try:
            if not self._container:
                raise AgentEnvironmentError(
                    "Cannot run any command in the container unless the container is started first.\n"
                    "Please make sure to use `.start()` method on this instance."
                )

            res = self._container.exec_run(
                cmd=[self.img_metadata.shell, "-c", cmd],
                stdout=True,
                stderr=True,
                demux=True,
            )
            stdout, stderr = res.output
            return Observation(
                content=(stdout.decode() if stdout else stderr.decode()),
                type="observation" if stdout else "observation_error",
                status_code=res.exit_code,
            )
        except docker.errors.APIError as e:
            return Observation(
                content=str(e),
                type="observation_error",
                status_code=e.status_code if e.status_code else 400,
            )
        except docker.errors.ContainerError as e:
            return Observation(
                content=e.stderr if e.stderr else str(e),
                type="observation_error",
                status_code=e.exit_status,
            )

    def stop(self):
        if self._container:
            self._container.stop()
            self._container.remove()
