import asyncio
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import TYPE_CHECKING, Any, AsyncIterator

from ..messages.base import Message
from ..messages.commons import Audio, Text
from .base import Node
from .registry import NodeFactory

if TYPE_CHECKING:
    from google.cloud import speech_v1p1beta1 as speech
    from google.api_core import exceptions
    from google.api_core.client_options import ClientOptions
try:
    from google.cloud import speech_v1p1beta1 as speech
    from google.api_core import exceptions
    from google.api_core.client_options import ClientOptions

    GOOLE_CLOUD_SPEECH_AVAILABLE = True
except ImportError:
    GOOLE_CLOUD_SPEECH_AVAILABLE = False


@NodeFactory.register("transcriber")
class TranscriberNode(Node[Audio, Text]):
    def __init__(
        self,
        input_channel: str,
        output_channel: str,
        rate: int,
        api_key: str,
        redis_url: str,
    ) -> None:
        if not GOOLE_CLOUD_SPEECH_AVAILABLE:
            raise ImportError(
                "Google Cloud Speech is not available. Please install"
                "aact with `pip install aact[google]` to use the TranscriberNode."
            )
        super().__init__(
            input_channel_types=[(input_channel, Audio)],
            output_channel_types=[(output_channel, Text)],
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.output_channel = output_channel
        self.rate: int = rate
        self.client: speech.SpeechAsyncClient = speech.SpeechAsyncClient(
            client_options=ClientOptions(  # type: ignore[no-untyped-call]
                api_key=api_key
            )
        )
        self.config: speech.RecognitionConfig = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code="en-US",
        )
        self.streaming_config: speech.StreamingRecognitionConfig = (
            speech.StreamingRecognitionConfig(config=self.config, interim_results=True)
        )
        self.queue = asyncio.Queue[bytes]()
        self.shutdown = asyncio.Event()

    async def transcribe(
        self,
    ) -> None:
        async def request_generator() -> (
            AsyncIterator[speech.StreamingRecognizeRequest]
        ):
            yield speech.StreamingRecognizeRequest(
                streaming_config=self.streaming_config
            )

            while not self.shutdown.is_set():
                content = await self.queue.get()
                yield speech.StreamingRecognizeRequest(audio_content=content)

        try:
            responses = await self.client.streaming_recognize(
                requests=request_generator()
            )
            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    await self.r.publish(
                        self.output_channel,
                        Message[Text](data=Text(text=transcript)).model_dump_json(),
                    )
        except exceptions.GoogleAPICallError as e:
            print(f"Error during transcription: {e}")

    async def __aenter__(self) -> Self:
        self.task = asyncio.create_task(self.transcribe())
        return await super().__aenter__()

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.shutdown.set()
        return await super().__aexit__(exc_type, exc_value, traceback)

    async def event_handler(
        self, input_channel: str, audio: Message[Audio]
    ) -> AsyncIterator[tuple[str, Message[Text]]]:
        if input_channel != self.input_channel:
            raise ValueError(f"Unexpected input channel: {input_channel}")
            yield "", Message[Text](data=Text(text=""))
        else:
            await self.queue.put(audio.data.audio)
