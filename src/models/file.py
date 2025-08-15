from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .project import Project

class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    path: str
    content: Optional[str] = None
    last_modified: Optional[datetime] = Field(default_factory=datetime.utcnow)
    project: Optional["Project"] = Relationship(back_populates="files")
