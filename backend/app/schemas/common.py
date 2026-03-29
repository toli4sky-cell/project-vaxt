from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class IdName(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class IdNameCode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None = None


class SignerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
