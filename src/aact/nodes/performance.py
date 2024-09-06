from datetime import datetime
from typing import AsyncIterator
from .base import Node
from .registry import NodeFactory

from ..messages import Message, Image, Tick
import os


@NodeFactory.register("performance")
class PerformanceMeasureNode(Node[Tick | Image, Image]):
    def __init__(
        self, input_channel: str, output_channel: str, message_size: int, redis_url: str
    ):
        super().__init__(
            input_channel_types=[
                (input_channel, Tick),
                (output_channel, Image),
            ],
            output_channel_types=[(output_channel, Image)],
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.output_channel = output_channel
        self.message_size = message_size
        self.message_to_datetime: dict[bytes, datetime] = {}

    async def _wait_for_input(self) -> AsyncIterator[tuple[str, Message[Tick | Image]]]:
        async for message in self.pubsub.listen():
            channel = message["channel"].decode("utf-8")
            now = datetime.now()
            if message["type"] == "message" and channel in self.input_channel_types:
                data = Message[self.input_channel_types[channel]].model_validate_json(  # type: ignore
                    message["data"]
                )
                decoded_time = datetime.now()
                if channel == self.output_channel:
                    print(f"Time to decode: {decoded_time - now}")
                yield channel, data
        raise Exception("Input channel closed unexpectedly")

    async def event_loop(
        self,
    ) -> None:
        async for input_channel, input_message in self._wait_for_input():
            async for output_channel, output_message in self.event_handler(
                input_channel, input_message
            ):
                json_str = output_message.model_dump_json()
                self.message_to_datetime[output_message.data.image[:16]] = (
                    datetime.now()
                )
                await self.r.publish(output_channel, json_str)

    async def event_handler(
        self, input_channel: str, input_message: Message[Tick | Image]
    ) -> AsyncIterator[tuple[str, Message[Image]]]:
        match input_message.data:
            case Tick(tick=_):
                size_in_bytes = self.message_size * 1024
                random_bytes = os.urandom(size_in_bytes)
                image = Image(image=random_bytes)
                yield self.output_channel, Message[Image](data=image)
            case Image(image=random_bytes):
                now = datetime.now()
                send_time = self.message_to_datetime[random_bytes[:16]]
                print(f"Latency: {now - send_time}")
                del self.message_to_datetime[random_bytes[:16]]
