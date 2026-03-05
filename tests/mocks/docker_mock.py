"""
Mock Docker client для изолированного тестирования бэкенда.

Заменяет реальный docker.DockerClient, чтобы тесты не создавали
настоящие контейнеры. Все операции записываются в in-memory хранилище.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeContainer:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    status: str = "created"
    attrs: dict = field(default_factory=dict)
    _image: str = ""
    _command: str | None = None

    @property
    def short_id(self) -> str:
        return self.id[:10]

    def start(self) -> None:
        self.status = "running"

    def stop(self, timeout: int = 10) -> None:
        self.status = "exited"

    def remove(self, force: bool = False) -> None:
        self.status = "removed"

    def kill(self, signal: str = "SIGKILL") -> None:
        self.status = "exited"

    def logs(self, **kwargs: Any) -> bytes:
        return b"mock container logs"

    def exec_run(self, cmd: str | list, **kwargs: Any) -> tuple[int, bytes]:
        return (0, b"mock exec output")

    def reload(self) -> None:
        pass


class FakeContainerCollection:
    def __init__(self) -> None:
        self._containers: dict[str, FakeContainer] = {}

    def run(
        self,
        image: str,
        command: str | None = None,
        name: str | None = None,
        detach: bool = False,
        **kwargs: Any,
    ) -> FakeContainer:
        container = FakeContainer(
            name=name or f"mock-{uuid.uuid4().hex[:8]}",
            status="running" if detach else "created",
            _image=image,
            _command=command,
        )
        container.attrs = {
            "NetworkSettings": {
                "IPAddress": f"172.17.0.{len(self._containers) + 2}",
                "Ports": kwargs.get("ports", {}),
            },
            "State": {"Status": container.status},
        }
        self._containers[container.id] = container
        return container

    def get(self, container_id: str) -> FakeContainer:
        if container_id in self._containers:
            return self._containers[container_id]
        for c in self._containers.values():
            if c.name == container_id:
                return c
        raise Exception(f"Container {container_id} not found")

    def list(self, **kwargs: Any) -> list[FakeContainer]:
        return list(self._containers.values())

    def create(self, image: str, **kwargs: Any) -> FakeContainer:
        return self.run(image, detach=False, **kwargs)


class FakeImageCollection:
    def pull(self, repository: str, tag: str | None = None, **kwargs: Any) -> Any:
        return {"status": "pulled", "repository": repository, "tag": tag}

    def get(self, name: str) -> dict:
        return {"id": uuid.uuid4().hex[:12], "tags": [name]}

    def list(self, **kwargs: Any) -> list[dict]:
        return []


class FakeNetworkCollection:
    def __init__(self) -> None:
        self._networks: list[dict] = []

    def create(self, name: str, **kwargs: Any) -> dict:
        network = {"id": uuid.uuid4().hex[:12], "name": name, **kwargs}
        self._networks.append(network)
        return network

    def list(self, **kwargs: Any) -> list[dict]:
        return self._networks


class MockDockerClient:
    """Drop-in replacement for docker.DockerClient in tests."""

    def __init__(self) -> None:
        self.containers = FakeContainerCollection()
        self.images = FakeImageCollection()
        self.networks = FakeNetworkCollection()

    def ping(self) -> bool:
        return True

    def info(self) -> dict:
        return {
            "Containers": len(self.containers._containers),
            "Images": 0,
            "ServerVersion": "mock-24.0.0",
        }

    def close(self) -> None:
        pass


def get_mock_docker_client() -> MockDockerClient:
    return MockDockerClient()
