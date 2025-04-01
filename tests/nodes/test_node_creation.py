import pytest
from aact.messages.base import DataModel
from aact.messages.registry import DataModelFactory
from aact.nodes import Node
from aact.nodes import NodeFactory


def test_node_with_non_datamodel_types():
    """Test that creating a node with non-DataModel types raises a TypeError."""

    class AWrong:
        pass

    class BWrong:
        pass

    # Create a node with non-DataModel types
    @NodeFactory.register("MyNode")
    class MyNode(Node[AWrong, BWrong]):  # type: ignore[type-var]
        def __init__(self) -> None:
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

    # Verify the correct error is raised
    with pytest.raises(TypeError) as excinfo:
        _ = MyNode()

    assert (
        "Input channel type <class 'test_node_creation.test_node_with_non_datamodel_types.<locals>.AWrong'> "
        "is not a subclass of DataModel" in str(excinfo.value)
    )


def test_node_with_unregistered_datamodel_types():
    """Test that creating a node with unregistered DataModel types raises a TypeError."""

    class ACorrect(DataModel):
        pass

    class BCorrect(DataModel):
        pass

    # Create a node with unregistered DataModel types
    @NodeFactory.register("MyNodeCorrect")
    class MyNodeCorrect(Node[ACorrect, BCorrect]):
        def __init__(self) -> None:
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

    # Verify the correct error is raised
    with pytest.raises(TypeError) as excinfo:
        _ = MyNodeCorrect()

    assert (
        "The input channel type <class 'test_node_creation.test_node_with_unregistered_datamodel_types.<locals>.ACorrect'> "
        "needs to be registered with `@DataModelFactory.register`" in str(excinfo.value)
    )


def test_node_with_registered_datamodel_types():
    """Test that creating a node with properly registered DataModel types succeeds."""

    @DataModelFactory.register("ACorrectNew")
    class ACorrectNew(DataModel):
        pass

    @DataModelFactory.register("BCorrectNew")
    class BCorrectNew(DataModel):
        pass

    # Create a node with registered DataModel types
    @NodeFactory.register("MyNodeCorrect")
    class MyNodeCorrect(Node[ACorrectNew, BCorrectNew]):
        def __init__(self) -> None:
            super().__init__(
                node_name="MyNode",
                input_channel_types=[("input", ACorrectNew)],
                output_channel_types=[("output", BCorrectNew)],
            )

        async def event_handler(
            self, input_channel: str, input_message: ACorrectNew
        ) -> None:  # type: ignore[override]
            # Handle the event
            pass

    # Verify that node creation succeeds
    node = MyNodeCorrect()
    assert isinstance(node, MyNodeCorrect)
