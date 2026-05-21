from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PixKeyItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uuid: str
    created_at: datetime
    updated_at: datetime
    key: str
    type: str
    status: str
    last_usage: datetime | None = None


class ListKeysDTOResponse(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[PixKeyItem]
