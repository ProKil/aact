from typing import AsyncIterator
from aact.messages.base import Message
from aact.messages.commons import (
    RestRequest,
    RestResponse,
    Tick,
    get_rest_request_class,
    get_rest_response_class,
    AnyDataModel,
)
from aact.nodes import Node, NodeFactory


@NodeFactory.register("api_client")
class APIClient(Node[Tick | RestResponse, RestRequest]):
    def __init__(
        self,
        input_tick_channel: str,
        input_response_channel: str,
        output_channel: str,
        redis_url: str,
    ):
        response_class = get_rest_response_class(AnyDataModel)
        request_class = get_rest_request_class(AnyDataModel)
        super().__init__(
            input_channel_types=[
                (input_tick_channel, Tick),
                (input_response_channel, response_class),
            ],
            output_channel_types=[(output_channel, request_class)],
            redis_url=redis_url,
        )

        self.request_class = request_class
        self.response_class = response_class
        self.input_tick_channel = input_tick_channel
        self.input_response_channel = input_response_channel
        self.output_channel = output_channel
        self.output_message_type: type[Message[RestRequest]] = Message[request_class]  # type: ignore[valid-type, assignment]

    async def event_handler(
        self, channel: str, message: Message[RestResponse | Tick]
    ) -> AsyncIterator[tuple[str, Message[RestRequest]]]:
        if channel == self.input_response_channel:
            print("Received response: ", message.data)
        elif channel == self.input_tick_channel:
            yield (
                self.output_channel,
                self.output_message_type(
                    data=self.request_class(
                        method="POST",
                        url="http://0.0.0.0:8080/spotify/auth/token",
                        data={"username": "test", "password": "test"},
                        content_type="application/x-www-form-urlencoded",
                    )
                ),
            )
        else:
            raise ValueError(f"Invalid channel: {channel}")
