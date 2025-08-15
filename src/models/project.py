from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .file import File

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: Optional[str] = Field(default="active")
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow)
    files: List["File"] = Relationship(back_populates="project")
