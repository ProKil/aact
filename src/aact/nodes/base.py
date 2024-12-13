from asyncio import CancelledError
import asyncio
import logging

from ..utils import Self
from typing import Any, AsyncIterator, Generic, Type, TypeVar
from pydantic import BaseModel, ConfigDict, ValidationError

from abc import abstractmethod
from ..messages import Message, Tick
from redis.asyncio import Redis

from ..messages.base import DataModel

InputType = TypeVar("InputType", covariant=True, bound=DataModel)
OutputType = TypeVar("OutputType", covariant=True, bound=DataModel)


class NodeExitSignal(CancelledError):
    """Node exit signal, which is raised in nodes' event handler. It is used to exit the node gracefully."""


class NodeConfigurationError(Exception):
    """Node configuration error, which is raised when the node configuration is incorrect."""


class Node(BaseModel, Generic[InputType, OutputType]):
    """
    Node is the base class for all nodes in the aact framework. It is a generic class that takes two type parameters:
    `InputType` and `OutputType`. The InputType and OutputType is used not only for static type checking but also for
    runtime message type validation, so it is important that you pass the correct types.

    Each of `InputType` and `OutputType` can be either:
    1. a subclass of `aact.messages.DataModel`, or
    2. a union of multiple `aact.DataModel` subclasses, or
    3. `aact.DataModel` itself to allow any type of message (not recommended).[^1]

    Any subclass of `aact.Node` must implement the `event_handler` method, which is the main computation logic of the
    node. The `event_handler` method takes two arguments: `input_channel` and `input_message`, and returns an async
    iterator of tuples of output channel and output message.

    For example, the following code snippet shows a simple node that takes a `aact.messages.Text` message from the `a`
    channel and echo it to the `b` channel.

    ```python
    from aact import Node, Message
    from aact.messages import Text

    from typing import AsyncIterator

    class EchoNode(Node[Text, Text]):
        def event_handler(self, input_channel: str, input_message: Message[Text]) -> AsyncIterator[str, Message[Text]]:
            yield "b", Message[Text](data=input_message.data)
    ```

    ## Built-in Nodes

    aact provides several built-in nodes that you can use out of the box. Here are some of the built-in nodes:

    - `aact.nodes.listener.ListenerNode`: A node that listens to the audio input from the microphone.
    - `aact.nodes.speaker.SpeakerNode`: A node that plays the audio output to the speaker.
    - `aact.nodes.record.RecordNode`: A node that records the messages to a file.
    - `aact.nodes.print.PrintNode`: A node that prints the messages to the console.
    - `aact.nodes.tick.TickNode`: A node that sends a tick message at a fixed interval.
    - `aact.nodes.random.RandomNode`: A node that sends a random number message.
    - `aact.nodes.transcriber.TranscriberNode`: A node that transcribes the audio messages to text.
    - `aact.nodes.tts.TTSNode`: A node that converts the text messages to audio.

    ## Common usage

    The usage of nodes is in the [quick start guide](aact.html/#usage).

    ## Advanced usage

    ### Send messages on your own

    The default behavior of sending messages in the base Node class is handled in the `event_loop` method. If you want to
    send messages on your own, you can directly use the Redis instance `r` to publish messages to the output channels.

    ```python

    class YourNode(Node[InputType, OutputType]):

        async def func_where_you_send_messages(self):
            await self.r.publish(your_output_channel, Message[OutputType](data=your_output_message).model_dump_json())

    ```

    ### Customize set up and tear down

    You can customize the set up and tear down of the node by overriding the `__aenter__` and `__aexit__` methods. For
    example, you can open a file in the `__aenter__` method and close it in the `__aexit__` method.

    ```python

    class YourNode(Node[InputType, OutputType]):

        async def __aenter__(self) -> Self:
            self.file = open("your_file.txt", "w")
            return await super().__aenter__()

        async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
            self.file.close()
            return await super().__aexit__(exc_type, exc_value, traceback)
    ```

    This will ensure the file is closed properly even if an exception is raised.

    ### Background tasks

    You can run background tasks in the node by creating a task in the `__aenter__` method and cancelling it in the
    `__aexit__` method.

    ```python

    class YourNode(Node[InputType, OutputType]):

        async def __aenter__(self) -> Self:

            self.task = asyncio.create_task(self.background_task())
            return await super().__aenter__()

        async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
            self.task.cancel()

            try:
                await self.task
            except asyncio.CancelledError:
                pass
    ```

    [^1]: Only if you know what you are doing. For example, in the `aact.nodes.record.RecordNode`, the `InputType` is
    `aact.messages.DataModel` because it can accept any type of message. But in most cases, you should specify the
    `InputType` and `OutputType` to be a specific subclass of `aact.messages.DataModel`.

    ### Shutdown nodes

    The default method for stopping nodes is through shutting down the subprocesses or RQ jobs. When you want to bring
    down the dataflow, you can `Ctrl + c` to turn off the nodes gracefully. 

    To shutdown a node itself, you can return from its event loop programatically when a certain condition is reached. 

    #### Experimental feature: Peer-stopping
    
    An experimental feature is peer-stopping. A node can not only stop itself but also other nodes. To do this, send
    a message to the channel `f"shutdown:{self.node_name}"` and the node manager will shutdown all of the nodes in the
    current dataflow. 
    """

    input_channel_types: dict[str, Type[InputType]]
    """
    A dictionary that maps the input channel names to the corresponding input message types.
    """
    output_channel_types: dict[str, Type[OutputType]]
    """
    A dictionary that maps the output channel names to the corresponding output message types.
    """
    node_name: str
    """
    The name of the node. When using NodeManger, the node name should be unique.
    """
    redis_url: str
    """
    The URL of the Redis server. It should be in the format of `redis://<host>:<port>/<db>`.
    """
    model_config = ConfigDict(extra="allow")
    """
    @private
    """

    def __init__(
        self,
        input_channel_types: list[tuple[str, Type[InputType]]],
        output_channel_types: list[tuple[str, Type[OutputType]]],
        node_name: str,
        redis_url: str = "redis://localhost:6379/0",
    ):
        try:
            BaseModel.__init__(
                self,
                input_channel_types=dict(input_channel_types),
                output_channel_types=dict(output_channel_types),
                node_name=node_name,
                redis_url=redis_url,
            )
        except ValidationError as _:
            raise NodeConfigurationError(
                "You passed an invalid configuration to the Node.\n"
                f"The required input channel types are: {self.model_fields['input_channel_types'].annotation}\n"
                f"The input channel types are: {input_channel_types}\n"
                f"The required output channel types are: {self.model_fields['output_channel_types'].annotation}\n"
                f"The output channel types are: {output_channel_types}\n"
            )
        self.r: Redis = Redis.from_url(redis_url)
        """
        @private
        """
        self.pubsub = self.r.pubsub()
        """
        @private
        """
        self.logger = logging.getLogger("aact.nodes.base.Node")
        """
        @private
        """
        self._background_tasks: list[asyncio.Task[None]] = []

    async def __aenter__(self) -> Self:
        try:
            await self.r.ping()
        except ConnectionError:
            raise ValueError(
                f"Could not connect to Redis with the provided url. {self.redis_url}"
            )
        await self.pubsub.subscribe(*self.input_channel_types.keys())
        self._background_tasks.append(asyncio.create_task(self._send_heartbeat()))
        return self

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await self.pubsub.unsubscribe()
        await self.r.aclose()

    async def _send_heartbeat(self) -> None:
        while True:
            await asyncio.sleep(1)
            await self.r.publish(
                f"heartbeat:{self.node_name}",
                Message[Tick](data=Tick(tick=0)).model_dump_json(),
            )

    async def _wait_for_input(
        self,
    ) -> AsyncIterator[tuple[str, Message[InputType]]]:
        async for message in self.pubsub.listen():
            channel = message["channel"].decode("utf-8")
            if message["type"] == "message" and channel in self.input_channel_types:
                try:
                    data = Message[
                        self.input_channel_types[channel]  # type: ignore[name-defined]
                    ].model_validate_json(message["data"])
                except ValidationError as e:
                    self.logger.error(
                        f"Failed to validate message from {channel}: {message['data']}. Error: {e}"
                    )
                    raise e
                yield channel, data
        raise Exception("Input channel closed unexpectedly")

    async def event_loop(
        self,
    ) -> None:
        """
        The main event loop of the node.
        The default implementation of the event loop is to wait for input messages from the input channels and call the
        `event_handler` method for each input message, and send each output message to the corresponding output channel.
        """
        try:
            async for input_channel, input_message in self._wait_for_input():
                async for output_channel, output_message in self.event_handler(
                    input_channel, input_message
                ):
                    await self.r.publish(
                        output_channel, output_message.model_dump_json()
                    )
        except NodeExitSignal as e:
            self.logger.info(f"Event loop cancelled: {e}. Exiting gracefully.")
        except Exception as e:
            raise e

    @abstractmethod
    async def event_handler(
        self, _: str, __: Message[InputType]
    ) -> AsyncIterator[tuple[str, Message[OutputType]]]:
        """
        @private
        """
        raise NotImplementedError("event_handler must be implemented in a subclass.")
        yield "", self.output_type()  # unreachable: dummy return value
