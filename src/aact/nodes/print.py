import asyncio
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import Any, AsyncIterator

from ..messages.commons import DataEntry

from .base import Node
from .registry import NodeFactory
from ..messages import DataModel, Zero, Message
from ..messages.registry import DataModelFactory

from aiofiles import stdout
from aiofiles.threadpool.text import AsyncTextIndirectIOWrapper


@NodeFactory.register("print")
class PrintNode(Node[DataModel, Zero]):
    def __init__(
        self,
        print_channel_types: dict[str, str],
        redis_url: str,
    ):
        input_channel_types: list[tuple[str, type[DataModel]]] = []
        for channel, channel_type_string in print_channel_types.items():
            input_channel_types.append(
                (channel, DataModelFactory.registry[channel_type_string])
            )

        super().__init__(
            input_channel_types=input_channel_types,
            output_channel_types=[],
            redis_url=redis_url,
        )
        self.output: AsyncTextIndirectIOWrapper | None = None
        self.write_queue: asyncio.Queue[DataEntry[DataModel]] = asyncio.Queue()
        self.write_task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Self:
        self.output = stdout
        self.write_task = asyncio.create_task(self.write_to_screen())
        return await super().__aenter__()

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        del self.output
        return await super().__aexit__(exc_type, exc_value, traceback)

    async def write_to_screen(self) -> None:
        while self.output:
            data_entry = await self.write_queue.get()
            await self.output.write(data_entry.model_dump_json() + "\n")
            await self.output.flush()
            self.write_queue.task_done()

    async def event_handler(
        self, input_channel: str, input_message: Message[DataModel]
    ) -> AsyncIterator[tuple[str, Message[Zero]]]:
        if input_channel in self.input_channel_types:
            await self.write_queue.put(
                DataEntry[self.input_channel_types[input_channel]](  # type: ignore[name-defined]
                    channel=input_channel, data=input_message.data
                )
            )
        else:
            yield input_channel, Message[Zero](data=Zero())
