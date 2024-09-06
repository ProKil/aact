import logging
from typing import Any, Callable, TypeVar

from ..messages.base import DataModel
from .base import Node

logger = logging.getLogger(__name__)
InputType = TypeVar("InputType", bound=DataModel)
OutputType = TypeVar("OutputType", bound=DataModel)


class NodeFactory:
    registry: dict[str, type[Node[DataModel, DataModel]]] = {}

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[
        [type[Node[InputType, OutputType]]], type[Node[InputType, OutputType]]
    ]:
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
        if name not in cls.registry:
            raise ValueError(f"Executor {name} not found in registry")
        return cls.registry[name](**kwargs)
