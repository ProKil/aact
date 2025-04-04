from typing import Any, AsyncIterator, Optional, TYPE_CHECKING

from ..utils import Self
from .base import Node
from .registry import NodeFactory
from ..messages import Audio, Zero, Message

# For type checking and IDE support
if TYPE_CHECKING:
    import pyaudio

# Runtime import
try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


@NodeFactory.register("speaker")
class SpeakerNode(Node[Audio, Zero]):
    def __init__(
        self,
        input_channel: str,
        node_name: str,
        redis_url: str,
        channels: int = 1,
        rate: int = 44100,
        format: int = pyaudio.paInt16 if PYAUDIO_AVAILABLE else 0,
    ):
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio is not available."
                "Please install aact with `pip install aact[audio]` to use the SpeakerNode."
            )

        super().__init__(
            input_channel_types=[(input_channel, Audio)],
            output_channel_types=[],
            node_name=node_name,
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.audio: "pyaudio.PyAudio" = pyaudio.PyAudio()
        self.stream: Optional["pyaudio.Stream"] = None
        self.channels = channels
        self.rate = rate
        self.format = format

    async def __aenter__(self) -> Self:
        if PYAUDIO_AVAILABLE:
            self.stream = self.audio.open(
                format=self.format, channels=self.channels, rate=self.rate, output=True
            )
        return await super().__aenter__()

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if PYAUDIO_AVAILABLE:
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
