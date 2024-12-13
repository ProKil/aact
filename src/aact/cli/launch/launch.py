import asyncio
import logging
import time
from typing import Annotated, Optional, TypeVar
from ..app import app
from ..reader import get_dataflow_config, draw_dataflow_mermaid, NodeConfig, Config
import typer

from ...nodes import NodeFactory


from ...utils import tomllib

from rq import Queue
from rq.exceptions import InvalidJobOperation
from rq.job import Job
from rq.command import send_stop_job_command
from redis import Redis

from ...manager import NodeManager

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")

logger = logging.getLogger(__name__)


async def _run_node(node_config: NodeConfig, redis_url: str) -> None:
    logger.info(f"Starting node {node_config}")
    try:
        async with NodeFactory.make(
            node_config.node_class,
            **node_config.node_args.model_dump(),
            node_name=node_config.node_name,
            redis_url=redis_url,
        ) as node:
            logger.info(f"Starting eventloop {node_config.node_name}")
            await node.event_loop()
    except Exception as e:
        logger.error(f"Error in node {node_config.node_name}: {e}")
        raise Exception(e)


def _sync_run_node(node_config: NodeConfig, redis_url: str) -> None:
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(_run_node(node_config, redis_url))
    except asyncio.CancelledError:
        logger = logging.getLogger(__name__)
        logger.info(f"Node {node_config.node_name} shutdown gracefully.")
    finally:
        loop.close()


@app.command()
def run_node(
    dataflow_toml: str = typer.Option(),
    node_name: str = typer.Option(),
    redis_url: str = typer.Option(),
) -> None:
    logger = logging.getLogger(__name__)
    config = Config.model_validate(tomllib.load(open(dataflow_toml, "rb")))
    logger.info(f"Starting dataflow with config {config}")
    # dynamically import extra modules
    for module in config.extra_modules:
        __import__(module)

    for nodes in config.nodes:
        if nodes.node_name == node_name:
            _sync_run_node(nodes, redis_url)
            break


def _import_extra_modules(extra_modules: list[str]) -> None:
    for module in extra_modules:
        __import__(module)


@app.command()
def run_dataflow(
    dataflow_toml: Annotated[
        str, typer.Argument(help="Configuration dataflow toml file")
    ],
    with_rq: Optional[bool] = typer.Option(
        False, help="Run the dataflow with RQ instead of asyncio."
    ),
    verbose: Optional[bool] = typer.Option(
        False, help="Print verbose logging for debugging."
    ),
) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    config = Config.model_validate(tomllib.load(open(dataflow_toml, "rb")))
    logger.info(f"Starting dataflow with config {config}")

    if with_rq:
        redis = Redis.from_url(config.redis_url)
        queue = Queue(connection=redis)
        job_ids: list[str] = []
        for node in config.nodes:
            job: Job = queue.enqueue(_sync_run_node, node, config.redis_url)
            job_ids.append(job.get_id())

        try:
            # Wait for all jobs to finish
            while not all(
                Job.fetch(job_id, connection=redis).get_status() == "finished"
                for job_id in job_ids
            ):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.warning("Terminating RQ jobs.")
            for job_id in job_ids:
                logger.info(f"Terminating job {job_id}")
                try:
                    send_stop_job_command(redis, job_id)  # stop the job if it's running
                except InvalidJobOperation:
                    logger.info(
                        f"Job {job_id} is not currently executing. Trying to delete it from queue."
                    )
                job = Job.fetch(job_id, connection=redis)
                job.delete()  # remove job from redis
                logger.info(
                    f"Job {job_id} has been terminated. Job status: {job.get_status()}"
                )
        finally:
            return

    with NodeManager(dataflow_toml, False, config.redis_url) as node_manager:
        node_manager.wait()


@app.command(help="A nice debugging feature. Draw dataflows with Mermaid.")
def draw_dataflow(
    dataflow_toml: Annotated[
        list[str],
        typer.Argument(
            help="Configuration dataflow toml files. "
            "You can provide multiple toml files to draw multiple dataflows on one graph."
        ),
    ],
    svg_path: Optional[str] = typer.Option(
        None,
        help="Path to save the svg file of the dataflow graph. "
        "If you don't set this, the mermaid code will be printed. "
        "If you set this, we will also render an svg picture of the dataflow graph.",
    ),
) -> None:
    dataflows = [
        get_dataflow_config(single_dataflow_toml)
        for single_dataflow_toml in dataflow_toml
    ]

    draw_dataflow_mermaid(dataflows, dataflow_toml, svg_path)
