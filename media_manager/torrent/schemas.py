import typing
import uuid
from enum import Enum

from pydantic import ConfigDict, BaseModel, Field

TorrentId = typing.NewType("TorrentId", uuid.UUID)


class Quality(Enum):
    uhd = 1
    fullhd = 2
    hd = 3
    sd = 4
    unknown = 5


class TorrentStatus(Enum):
    finished = 1
    downloading = 2
    error = 3
    unknown = 4


class Torrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: TorrentId = Field(default_factory=uuid.uuid4)
    status: TorrentStatus
    title: str
    quality: Quality
    imported: bool
    hash: str
