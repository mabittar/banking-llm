from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PixKeyItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    key: str
    type: str
    status: str
    last_usage: datetime | None = Field(None, alias="lastUsage")


class ListKeysDTOResponse(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[PixKeyItem]
