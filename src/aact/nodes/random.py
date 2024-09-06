from typing import AsyncIterator


from .base import Node
from .registry import NodeFactory
from ..messages import Tick, Float, Message
import random


@NodeFactory.register("random")
class RandomNode(Node[Tick, Float]):
    def __init__(
        self,
        input_channel: str,
        output_channel: str,
        redis_url: str = "redis://localhost:6379/0",
    ):
        super().__init__(
            input_channel_types=[(input_channel, Tick)],
            output_channel_types=[(output_channel, Float)],
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.output_channel = output_channel

    async def event_handler(
        self, _: str, __: Message[Tick]
    ) -> AsyncIterator[tuple[str, Message[Float]]]:
        yield self.output_channel, Message[Float](data=Float(value=random.random()))
