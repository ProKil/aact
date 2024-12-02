import asyncio
import datetime
from logging import Logger
import os
import signal
from subprocess import Popen
import threading
from ..utils import tomllib
from typing import Any, Literal
from uuid import uuid4

from redis.asyncio import Redis
from redis import Redis as SyncRedis

from ..cli.reader import Config

from ..utils import Self

logger = Logger("NodeManager")

Health = Literal["Started", "Running", "No Response", "Stopped"]


def run_event_loop_in_thread() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()


class NodeManager(object):
    def __init__(
        self,
        dataflow_toml: str,
        with_rq: bool = False,
        redis_url: str = "redis://localhost:6379/0",
    ):
        self.id = f"manager-{str(uuid4())}"
        self.dataflow_toml = dataflow_toml
        self.with_rq = with_rq
        self.subprocesses: dict[str, Popen[bytes]] = {}
        self.pubsub = Redis.from_url(redis_url).pubsub()
        self.shutdown_pubsub = SyncRedis.from_url(redis_url).pubsub()  # type: ignore[no-untyped-call]
        self.background_tasks: list[asyncio.Task[None]] = []
        self.node_health: dict[str, Health] = {}
        self.last_heartbeat: dict[str, float] = {}
        self.loop: asyncio.AbstractEventLoop | None = None
        self.shutdown_signal: bool = False

    def __enter__(
        self,
    ) -> Self:
        config = Config.model_validate(tomllib.load(open(self.dataflow_toml, "rb")))

        # Nodes that run w/ subprocess
        for node in config.nodes:
            try:
                command = f"aact run-node --dataflow-toml {self.dataflow_toml} --node-name {node.node_name} --redis-url {config.redis_url}"
                node_process = Popen(
                    [command],
                    shell=True,
                    preexec_fn=os.setsid,  # Start the subprocess in a new process group
                )
                logger.info(
                    f"Starting subprocess {node_process} for node {node.node_name}"
                )
                assert (
                    node.node_name not in self.subprocesses
                ), f"Node {node.node_name} is duplicated."
                self.subprocesses[node.node_name] = node_process
                self.node_health[node.node_name] = "Started"
            except Exception as e:
                logger.error(
                    f"Error starting subprocess {node.node_name}: {e}. Stopping other nodes as well."
                )
                for node_name, node_process in self.subprocesses.items():
                    logger.info(
                        f"Terminating Node {node_name}. Process: {node_process}"
                    )
                    try:
                        os.killpg(os.getpgid(node_process.pid), signal.SIGTERM)
                    except ProcessLookupError:
                        logger.info(f"Process group {node_process.pid} not found.")
                self.subprocesses = {}
                raise e

        thread = threading.Thread(target=run_event_loop_in_thread, daemon=True)
        thread.start()
        self.loop = asyncio.get_event_loop()

        self.background_tasks.append(self.loop.create_task(self.wait_for_heartbeat()))
        self.background_tasks.append(self.loop.create_task(self.update_health_status()))

        return self

    async def wait_for_heartbeat(
        self,
    ) -> None:
        for node_name in self.subprocesses.keys():
            await self.pubsub.subscribe(f"heartbeat:{node_name}")

        async for message in self.pubsub.listen():
            node_name = ":".join(message["channel"].decode("utf-8").split(":")[1:])
            self.last_heartbeat[node_name] = datetime.datetime.now().timestamp()

    async def update_health_status(
        self,
    ) -> None:
        while True:
            for node_name, last_heartbeat in self.last_heartbeat.items():
                if datetime.datetime.now().timestamp() - last_heartbeat > 10:
                    self.node_health[node_name] = "No Response"
                else:
                    self.node_health[node_name] = "Running"
            await asyncio.sleep(1)

    def wait(
        self,
    ) -> None:
        for node_name in self.subprocesses.keys():
            self.shutdown_pubsub.subscribe(f"shutdown:{node_name}")
        for message in self.shutdown_pubsub.listen():
            node_name = ":".join(message["channel"].decode("utf-8").split(":")[1:])
            if message["data"] == b"shutdown":
                logger.info(f"Received shutdown signal for node {node_name}")
                self.shutdown_signal = True
                break
        self.shutdown_pubsub.unsubscribe()
        self.shutdown_pubsub.close()

    def __exit__(
        self,
        signum: int | None = None,
        frame: Any | None = None,
        traceback: Any | None = None,
    ) -> None:
        for _, node_process in self.subprocesses.items():
            try:
                os.killpg(os.getpgid(node_process.pid), signal.SIGTERM)
                logger.info(f"Terminating process group {node_process.pid}")
            except ProcessLookupError:
                logger.warning(f"Process group {node_process.pid} not found.")
        for task in self.background_tasks:
            task.cancel()

        if self.loop:
            self.loop.run_until_complete(self.pubsub.unsubscribe())
            self.loop.run_until_complete(self.pubsub.close())
            self.loop.stop()
