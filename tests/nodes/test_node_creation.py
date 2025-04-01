import pytest
from aact.messages.base import DataModel
from aact.messages.registry import DataModelFactory
from aact.nodes import Node
from aact.nodes import NodeFactory


def test_create_node() -> None:
    class AWrong:
        pass

    class BWrong:
        pass

    # Create a new node
    @NodeFactory.register("MyNode")
    class MyNode(Node[AWrong, BWrong]):  # type: ignore[type-var]
        def __init__(
            self,
        ) -> None:
            super().__init__(
                node_name="MyNode",
                input_channel_types=[("input", AWrong)],
                output_channel_types=[("output", BWrong)],
            )

        async def event_handler(
            self, input_channel: str, input_message: AWrong
        ) -> None:  # type: ignore[override]
            # Handle the event
            pass

    @DataModelFactory.register("data_model_a")
    class ACorrect(DataModel):
        pass

    @DataModelFactory.register("data_model_b")
    class BCorrect(DataModel):
        pass

    # Create a new node
    @NodeFactory.register("MyNodeCorrect")
    class MyNodeCorect(Node[ACorrect, BCorrect]):
        def __init__(
            self,
        ) -> None:
            super().__init__(
                node_name="MyNode",
                input_channel_types=[("input", ACorrect)],
                output_channel_types=[("output", BCorrect)],
            )

        async def event_handler(
            self, input_channel: str, input_message: ACorrect
        ) -> None:  # type: ignore[override]
            # Handle the event
            pass

    # Create an instance of the node
    with pytest.raises(TypeError) as excinfo:
        _ = MyNode()

    assert (
        "Input channel type <class 'test_node_creation.test_create_node.<locals>.AWrong'> is not a subclass of DataModel"
        in str(excinfo.value)
    )

    _ = MyNodeCorect()
