import asyncio
import sys
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import Any, AsyncIterator

import pyaudio

from ..messages.base import DataModel, Message
from .base import Node
from .registry import NodeFactory
from ..messages import Zero, Audio


@NodeFactory.register("listener")
class ListenerNode(Node[Zero, Audio]):
    def __init__(self, output_channel: str, redis_url: str):
        super().__init__(
            input_channel_types=[],
            output_channel_types=[(output_channel, Audio)],
            redis_url=redis_url,
        )
        self.output_channel = output_channel
        self.audio = pyaudio.PyAudio()
        self.stream: pyaudio.Stream | None = None
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Self:
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.callback,
        )
        self.task = asyncio.create_task(self.send_frames())
        return await super().__aenter__()

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        return await super().__aexit__(_, __, ___)

    async def send_frames(self) -> None:
        while True:
            frames = await self.queue.get()
            await self.r.publish(
                self.output_channel,
                Message[Audio](data=Audio(audio=frames)).model_dump_json(),
            )

    def callback(
        self, in_data: bytes | None, _: Any, __: Any, ___: Any
    ) -> tuple[None, int]:
        if in_data:
            self.queue.put_nowait(in_data)
        return None, pyaudio.paContinue

    async def event_loop(self) -> None:
        while True:
            await asyncio.sleep(1)

    async def event_handler(
        self, _: str, __: Message[Zero]
    ) -> AsyncIterator[tuple[str, Message[Audio]]]:
        raise NotImplementedError("ListenerNode does not have an event handler.")
        yield "", Message[DataModel](data=Zero())
