from datetime import datetime
from typing import Any, Annotated, Generic, TypeVar

from .registry import DataModelFactory
from .base import DataModel
from pydantic import (
    ConfigDict,
    Field,
    PlainValidator,
    PlainSerializer,
    WithJsonSchema,
    BaseModel,
    create_model,
)


@DataModelFactory.register("zero")
class Zero(DataModel):
    pass


@DataModelFactory.register("any")
class AnyDataModel(DataModel):
    model_config = ConfigDict(extra="allow")


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


@DataModelFactory.register("rest_request")
class RestRequest(DataModel):
    url: str
    method: str
    data: DataModel | None
    content_type: str = Field(default="application/json")


@DataModelFactory.register("rest_response")
class RestResponse(DataModel):
    status_code: int
    data: DataModel | None


def get_rest_request_class(data_model: type[T]) -> type[RestRequest]:
    new_class = create_model(
        f"RestRequest[{data_model.__name__}]",
        __base__=RestRequest,
        data=(data_model | None, None),
    )
    return new_class


def get_rest_response_class(data_model: type[T]) -> type[RestResponse]:
    new_class = create_model(
        f"RestResponse[{data_model.__name__}]",
        __base__=RestResponse,
        data=(data_model | None, None),
    )
    return new_class
