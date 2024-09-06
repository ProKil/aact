import logging
from typing import Any, Callable, Literal, TypeVar
from pydantic import create_model

from .base import DataModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DataModel)


class DataModelFactory:
    registry: dict[str, type[DataModel]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[T]], type[T]]:
        def inner_wrapper(wrapped_class: type[T]) -> type[T]:
            if name in cls.registry:
                logger.warning("DataModel %s already exists. Will replace it", name)
            new_class = create_model(
                cls.__name__,
                __base__=wrapped_class,
                data_type=(Literal[name], name),
            )
            cls.registry[name] = new_class
            return new_class

        return inner_wrapper

    @classmethod
    def make(cls, name: str, **kwargs: Any) -> DataModel:
        if name not in cls.registry:
            raise ValueError(f"DataModel {name} not found in registry")
        instance: DataModel = cls.registry[name](**kwargs)
        return instance
