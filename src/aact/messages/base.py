from pydantic import BaseModel, Field

from typing import Generic, Literal, TypeVar


class DataModel(BaseModel):
    """
    # DataModel

    A datamodel in `aact` is a pydantic BaseModel with an additional field `data_type` to differentiate between different message types.

    Here are the built-in data models:

    - `aact.message.Tick`: A data model with a single field `tick` of type `int`. This is useful for sending clock ticks.
    - `aact.messages.Float`: A data model with a single field `value` of type `float`. This is useful for sending floating-point numbers.
    - `aact.messages.Image`: A data model with a single field `image` of type `bytes`. This is useful for sending images.
    - `aact.messages.Text`: A data model with a single field `text` of type `str`. This is useful for sending text messages.
    - `aact.messages.Audio`: A data model with a single field `audio` of type `bytes`. This is useful for sending audio files.
    - `aact.messages.Zero`: A dummy data model with no fields. This is useful when the nodes do not receive or send any data.

    ## Customize DataModels

    For custimizing your own data models, here is an example:

    ```python

    from aact.messages import DataModel, DataModelFactory


    @DataModelFactory.register("my_data_model")
    class MyDataModel(DataModel):
        my_field: str
    ```

    You can see that you don't need to define the `data_type` field in your custom data models. The `DataModelFactory` will take care of it for you.
    """

    data_type: Literal[""] = Field("")
    """
    @private
    """


T = TypeVar("T", bound=DataModel)


class Message(BaseModel, Generic[T]):
    """
    # Messages
    Message class is the base class for all of the messages passing through the channels.
    It is a pydantic BaseModel with a single field `data` containing the actual data.
    The `data` field is a subclass of `aact.messages.DataModel`.

    ## Usage

    To create a message type with DataModel `T`, you can use `Message[T]`.
    To initialize a message, you can use `Message[T](data=your_data_model_instance)`.

    <details>

    <summary> Why have an additional wrapper over DataModel? </summary>

    The reason for having a separate class for messages is to leverage the [pydantic's tagged union feature](https://docs.pydantic.dev/latest/concepts/performance/#use-tagged-union-not-union).
    This allows us to differentiate between different message types at runtime.

    For example, the following code snippet shows how to decide the message type at runtime:

    ```python
    from aact import Message, DataModel
    from aact.messages import Image, Tick

    tick = 123
    tick_message = Message[Tick](data=Tick(tick=tick))
    tick_message_json = tick_message.model_dump_json()

    possible_image_or_tick_message = Message[Tick | Image].model_validate_json(
        tick_message_json
    )
    assert isinstance(possible_image_or_tick_message.data, Tick)
    ```
    </details>
    """

    data: T = Field(discriminator="data_type")
    """
    @private
    """
