from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from .enums import ProjectStatus

if TYPE_CHECKING:
    from .file import File
    from .file_meta import FileMeta

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: ProjectStatus = Field(default=ProjectStatus.NEW)
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow)
    files: List["File"] = Relationship(back_populates="project")
    file_metas: List["FileMeta"] = Relationship(back_populates="project")
