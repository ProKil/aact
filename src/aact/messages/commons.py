from datetime import datetime
from typing import Any, Annotated, Generic, TypeVar

from .registry import DataModelFactory
from .base import DataModel
from pydantic import Field, PlainValidator, PlainSerializer, WithJsonSchema, BaseModel


@DataModelFactory.register("zero")
class Zero(DataModel):
    pass


@DataModelFactory.register("tick")
class Tick(DataModel):
    tick: int


@DataModelFactory.register("float")
class Float(DataModel):
    value: float


def hex_bytes_validator(o: Any) -> bytes:
    if isinstance(o, bytes):
        return o
    elif isinstance(o, bytearray):
        return bytes(o)
    elif isinstance(o, str):
        return bytes.fromhex(o)
    raise ValueError(f"Expected bytes, bytearray, or hex string, got {type(o)}")


HexBytes = Annotated[
    bytes,
    PlainValidator(hex_bytes_validator),
    PlainSerializer(lambda b: b.hex()),
    WithJsonSchema({"type": "string"}),
]


@DataModelFactory.register("image")
class Image(DataModel):
    image: HexBytes


@DataModelFactory.register("text")
class Text(DataModel):
    text: str


@DataModelFactory.register("audio")
class Audio(DataModel):
    audio: HexBytes


T = TypeVar("T", bound=DataModel)


class DataEntry(BaseModel, Generic[T]):
    timestamp: datetime = Field(default_factory=datetime.now)
    channel: str
    data: T
