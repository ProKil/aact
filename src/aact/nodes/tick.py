import asyncio
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from typing import AsyncIterator

from ..messages import Tick, Message, Zero
from .base import Node
from .registry import NodeFactory
import time


@NodeFactory.register("tick")
class TickNode(Node[Zero, Tick]):
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        super().__init__(
            input_channel_types=[],
            output_channel_types=[
                ("tick/millis/10", Tick),
                ("tick/millis/20", Tick),
                ("tick/millis/33", Tick),
                ("tick/millis/50", Tick),
                ("tick/millis/100", Tick),
                ("tick/secs/1", Tick),
            ],
            redis_url=redis_url,
        )

    async def tick_at_given_interval(self, channel: str, interval: float) -> None:
        tick_count = 0
        last: float | None = None
        last_sleep = interval
        while True:
            await self.r.publish(
                channel, Message[Tick](data=Tick(tick=tick_count)).model_dump_json()
            )
            tick_count += 1
            now = time.time()
            if last is not None:
                last_sleep = last_sleep - (now - last - interval)
            await asyncio.sleep(last_sleep)
            last = now

    async def event_loop(self) -> None:
        await asyncio.gather(
            self.tick_at_given_interval("tick/millis/10", 0.01),
            self.tick_at_given_interval("tick/millis/20", 0.02),
            self.tick_at_given_interval("tick/millis/33", 0.033),
            self.tick_at_given_interval("tick/millis/50", 0.05),
            self.tick_at_given_interval("tick/millis/100", 0.1),
            self.tick_at_given_interval("tick/secs/1", 1.0),
        )

    async def __aenter__(self) -> Self:
        return await super().__aenter__()

    async def event_handler(
        self, _: str, __: Message[Zero]
    ) -> AsyncIterator[tuple[str, Message[Tick]]]:
        raise NotImplementedError("TickNode does not have an event handler.")
        yield "", Message[Tick](data=Tick(tick=0))
