from typing import AsyncIterator
from aact import Node, NodeFactory
from aact.messages import Message, Text

from openai import OpenAI


@NodeFactory.register("gpt4_text_chatbot_node")
class GPT4TextChatbotNode(Node[Text, Text]):
    def __init__(self, input_channel: str, output_channel: str, redis_url: str):
        super().__init__(
            input_channel_types=[(input_channel, Text)],
            output_channel_types=[(output_channel, Text)],
            redis_url=redis_url,
        )
        self.input_channel = input_channel
        self.output_channel = output_channel
        self.client = OpenAI()

    async def event_handler(
        self, channel: str, message: Message[Text]
    ) -> AsyncIterator[tuple[str, Message[Text]]]:
        match channel:
            case self.input_channel:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": message.data.text},
                    ],
                )
                yield (
                    self.output_channel,
                    Message[Text](data=Text(text=response.choices[0].message.content)),
                )
            case _:
                raise ValueError(f"Unexpected channel: {channel}")
