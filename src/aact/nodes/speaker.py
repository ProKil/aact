import sys
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import Any, AsyncIterator
import pyaudio
from .base import Node
from .registry import NodeFactory
from ..messages import Audio, Zero, Message


@NodeFactory.register("speaker")
class SpeakerNode(Node[Audio, Zero]):
    def __init__(
        self,
        input_channel: str,
        redis_url: str,
    ):
        super().__init__(
            input_channel_types=[(input_channel, Audio)],
            output_channel_types=[],
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.audio = pyaudio.PyAudio()
        self.stream: pyaudio.Stream | None = None

    async def __aenter__(self) -> Self:
        self.stream = self.audio.open(
            format=pyaudio.paInt16, channels=1, rate=44100, output=True
        )

        return await super().__aenter__()

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        return await super().__aexit__(_, __, ___)

    async def event_handler(
        self, input_channel: str, message: Message[Audio]
    ) -> AsyncIterator[tuple[str, Message[Zero]]]:
        if input_channel == self.input_channel:
            if self.stream:
                self.stream.write(message.data.audio)
            else:
                raise ValueError(
                    "Stream is not initialized. Please use the async context manager."
                )
        else:
            yield "", Message[Zero](data=Zero())
