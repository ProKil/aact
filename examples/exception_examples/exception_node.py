from typing import AsyncIterator
from aact.nodes import Node, NodeFactory
from aact.messages import Text
from aact import Message


@NodeFactory.register("exception_node")
class ExceptionNode(Node[Text, Text]):
    def event_handler(
        self, input_channel: str, input_message: Message[Text]
    ) -> AsyncIterator[tuple[str, Message[Text]]]:
        raise Exception("This is an exception from the node.")
