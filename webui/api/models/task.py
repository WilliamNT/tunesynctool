from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from api.models.search import validate_provider
from api.models.track import TrackRead

class TaskStatus(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    QUEUED = "queued"
    CANCELED = "canceled"
    ON_HOLD = "on_hold"

class PlaylistTransferCreate(BaseModel):
    """
    Playlist transfer parameters.
    """

    from_provider: str = Field(description="Origin provider for the playlist.")
    from_playlist: str = Field(description="Source playlist you wish to replicate.")
    to_provider: str = Field(description="Target provider to replicate the playlist on.")
    
    @field_validator("from_provider")
    def validate_from_provider(cls, v: str) -> str:
        return validate_provider(v)

    @field_validator("to_provider")
    def validate_to_provider(cls, v: str) -> str:
        return validate_provider(v)
    
class TaskResponseBase(BaseModel):
    """
    Base class for task responses.
    """

    task_id: UUID = Field(description="Unique identifier for the task.")
    status: TaskStatus = Field(description="Current status of the task as a whole.")
    status_reason: Optional[str] = Field(description="Optional reason for the status to be shown to end users or used in logs.", default=None)
    queued_at: int = Field(description="Unix timestamp in UTC to help tell when the task was put in the queue.")
    done_at: Optional[int] = Field(description="Unix timestamp in UTC to help tell when the task was considered done.", default=None)

class PlaylistTaskProgress(BaseModel):
    """
    Current progress of a playlist transfer or sync task.
    """

    track: Optional[TrackRead] = Field(description="The track that is being processed at the time of request.", default=None)
    handled: int = Field(description="How many tracks have been already processed.", default=0)
    in_queue: int = Field(description="How many tracks are in queue to be processed.", default=0)

class PlaylistTaskStatus(TaskResponseBase):
    """
    Status of the playlist transfer.
    """

    arguments: PlaylistTransferCreate = Field(description="Original request parameters.")
    progress: PlaylistTaskProgress = Field(description="Details about the progress of the task.")