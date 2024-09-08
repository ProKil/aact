import asyncio
import sys
from typing import Any, AsyncIterator, Optional, TYPE_CHECKING

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from ..messages.base import DataModel, Message
from .base import Node
from .registry import NodeFactory
from ..messages import Zero, Audio

# For type checking and IDE support
if TYPE_CHECKING:
    import pyaudio

# Runtime import
try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


@NodeFactory.register("listener")
class ListenerNode(Node[Zero, Audio]):
    def __init__(self, output_channel: str, redis_url: str):
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio is not available."
                "Please install aact with `pip install aact[audio]` to use the ListenerNode."
            )

        super().__init__(
            input_channel_types=[],
            output_channel_types=[(output_channel, Audio)],
            redis_url=redis_url,
        )
        self.output_channel = output_channel
        self.audio: "pyaudio.PyAudio" = pyaudio.PyAudio()
        self.stream: Optional["pyaudio.Stream"] = None
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.task: Optional[asyncio.Task[None]] = None

    async def __aenter__(self) -> Self:
        if PYAUDIO_AVAILABLE:
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
        if PYAUDIO_AVAILABLE:
            self.audio.terminate()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        return await super().__aexit__(_, __, ___)

    async def send_frames(self) -> None:
        while True:
            frames = await self.queue.get()
            await self.r.publish(
                self.output_channel,
                Message[Audio](data=Audio(audio=frames)).model_dump_json(),
            )

    def callback(
        self, in_data: Optional[bytes], _: Any, __: Any, ___: Any
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
