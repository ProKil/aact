import asyncio
import json
import logging
from typing import AsyncIterator, TypeVar
from . import Node, NodeFactory

from ..messages.base import Message
from ..messages.commons import (
    RestRequest,
    RestResponse,
    get_rest_response_class,
    get_rest_request_class,
)

import aiohttp

from ..messages.registry import DataModelFactory

T = TypeVar("T", bound=RestResponse)


logger = logging.getLogger(__name__)


async def _parse_response(
    response: aiohttp.ClientResponse, response_class: type[T]
) -> T:
    status_code = response.status

    try:
        if response.content_type == "application/json":
            json_data = await response.json()
            # Only try to parse data into model if we have a successful response
            if 200 <= status_code < 300 and json_data:
                return response_class(status_code=status_code, data=json_data)
    except (json.JSONDecodeError, ValueError) as e:
        # Log error here if needed
        logger.error(f"Error parsing response: {e}")
        pass

    logger.warning(f"{response}")
    return response_class(status_code=status_code, data=None)


@NodeFactory.register("rest_api")
class RestAPINode(Node[RestRequest, RestResponse]):
    """
    A node that sends a REST request to a given URL and sends the response to an output channel.

    Args:

    - `input_channel`: The input channel to listen for RestRequest messages.
    - `output_channel`: The output channel to send RestResponse messages.
    - `output_type_str`: The string identifier of the DataModel to parse the response into.
    - `redis_url`: The URL of the Redis server to connect to.

    REST API Node Example:

    ```toml

    [[nodes]]

    node_name = "rest_api"
    node_class = "rest_api"

    [[nodes.node_args]]

    input_channel = "rest_request"
    output_channel = "rest_response"
    output_type_str = "float"
    ```
    """

    def __init__(
        self,
        input_channel: str,
        output_channel: str,
        input_type_str: str,
        output_type_str: str,
        node_name: str,
        redis_url: str,
    ):
        if input_type_str not in DataModelFactory.registry:
            raise ValueError(
                f"DataModel {input_type_str} is used as the input data model, but not found in registry"
            )

        if output_type_str not in DataModelFactory.registry:
            raise ValueError(
                f"DataModel {output_type_str} is used as the output data model, but not found in registry"
            )

        request_class = get_rest_request_class(
            DataModelFactory.registry[input_type_str]
        )
        response_data_class = DataModelFactory.registry[output_type_str]
        response_class = get_rest_response_class(response_data_class)

        super().__init__(
            input_channel_types=[(input_channel, request_class)],
            output_channel_types=[(output_channel, response_class)],
            node_name=node_name,
            redis_url=redis_url,
        )

        self.input_channel = input_channel
        self.output_channel = output_channel
        self.shutdown_event: asyncio.Event = asyncio.Event()
        self.request_class = request_class
        self.response_class = response_class
        self.response_data_class = response_data_class

    async def __aenter__(self) -> "RestAPINode":
        await super().__aenter__()
        return self

    async def handle_request(self, message: RestRequest) -> None:
        if message.content_type == "application/json":
            async with aiohttp.request(
                message.method,
                message.url,
                json=message.data.model_dump_json() if message.data else None,
            ) as response:
                response_data = await _parse_response(response, self.response_class)
        else:
            async with aiohttp.request(
                message.method,
                message.url,
                data=message.data.model_dump(exclude={"data_type"})
                if message.data
                else None,
                headers={"Content-Type": message.content_type},
            ) as response:
                response_data = await _parse_response(response, self.response_class)
        await self.r.publish(
            self.output_channel,
            Message[self.response_class](data=response_data).model_dump_json(),  # type: ignore[name-defined]
        )

    async def event_handler(
        self, channel: str, message: Message[RestRequest]
    ) -> AsyncIterator[tuple[str, Message[RestResponse]]]:
        if channel == self.input_channel:
            await self.handle_request(message.data)
        else:
            raise ValueError(f"Unexpected channel {channel}")
            yield  # This is needed to make this function a generator
