import logging
from typing import Any, Callable, TypeVar

from ..messages.base import DataModel
from .base import Node

logger = logging.getLogger(__name__)
InputType = TypeVar("InputType", bound=DataModel)
OutputType = TypeVar("OutputType", bound=DataModel)


class NodeFactory:
    """
    To use nodes in the dataflow, you need to register them in the NodeFactory before using them.
    The reason for this is to allow users write string names in toml files which can be converted
    to actual classes at runtime.

    To register a node, you need to use the `@NodeFactory.register` decorator.

    Example:
    ```python
    from aact import Node, NodeFactory

    @NodeFactory.register("node_name")
    class YourNode(Node[your_input_type, your_output_type]):
        # Your implementation of the node
    ```

    <details>

    <summary> For power users </summary>

    You can initialize a node using the `NodeFactory.make` method.

    ```python
    from aact import NodeFactory

    node = NodeFactory.make("node_name", ...)# your arguments
    ```
    """

    registry: dict[str, type[Node[DataModel, DataModel]]] = {}
    """
    @private
    """

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[
        [type[Node[InputType, OutputType]]], type[Node[InputType, OutputType]]
    ]:
        """
        @private
        """

        def inner_wrapper(
            wrapped_class: type[Node[InputType, OutputType]],
        ) -> type[Node[InputType, OutputType]]:
            if name in cls.registry:
                logger.warning("Executor %s already exists. Will replace it", name)
            cls.registry[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def make(cls, name: str, **kwargs: Any) -> Node[DataModel, DataModel]:
        """
        @private
        """
        if name not in cls.registry:
            raise ValueError(f"Executor {name} not found in registry")
        return cls.registry[name](**kwargs)
