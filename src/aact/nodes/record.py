import asyncio
from datetime import datetime
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

from aiofiles import open
from aiofiles.threadpool.text import AsyncTextIOWrapper
from aiofiles.base import AiofilesContextManager


@NodeFactory.register("record")
class RecordNode(Node[DataModel, Zero]):
    def __init__(
        self,
        record_channel_types: dict[str, str],
        jsonl_file_path: str,
        redis_url: str,
        add_datetime: bool = True,
    ):
        input_channel_types: list[tuple[str, type[DataModel]]] = []
        for channel, channel_type_string in record_channel_types.items():
            input_channel_types.append(
                (channel, DataModelFactory.registry[channel_type_string])
            )
        if add_datetime:
            # add a datetime to jsonl_file_path before the extension. The file can have any extension.
            jsonl_file_path = (
                jsonl_file_path[: jsonl_file_path.rfind(".")]
                + datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")
                + jsonl_file_path[jsonl_file_path.rfind(".") :]
            )

        super().__init__(
            input_channel_types=input_channel_types,
            output_channel_types=[],
            redis_url=redis_url,
        )
        self.jsonl_file_path = jsonl_file_path
        self.aioContextManager: AiofilesContextManager[AsyncTextIOWrapper] | None = None
        self.json_file: AsyncTextIOWrapper | None = None
        self.write_queue: asyncio.Queue[DataEntry[DataModel]] = asyncio.Queue()
        self.write_task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Self:
        self.aioContextManager = open(self.jsonl_file_path, "w")
        self.json_file = await self.aioContextManager.__aenter__()
        self.write_task = asyncio.create_task(self.write_to_file())
        return await super().__aenter__()

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if self.aioContextManager:
            await self.aioContextManager.__aexit__(exc_type, exc_value, traceback)
        del self.json_file
        return await super().__aexit__(exc_type, exc_value, traceback)

    async def write_to_file(self) -> None:
        while self.json_file:
            data_entry = await self.write_queue.get()
            await self.json_file.write(data_entry.model_dump_json() + "\n")
            await self.json_file.flush()
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
