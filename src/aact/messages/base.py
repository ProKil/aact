from pydantic import BaseModel, Field

from typing import Generic, Literal, TypeVar


class DataModel(BaseModel):
    data_type: Literal[""] = Field("")


T = TypeVar("T", bound=DataModel)


class Message(BaseModel, Generic[T]):
    data: T = Field(discriminator="data_type")
