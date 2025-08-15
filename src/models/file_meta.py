from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship

if TYPE_CHECKING:
    from .project import Project


class FileMeta(SQLModel, table=True):
    """Stored metadata for indexed files."""

    __table_args__ = (UniqueConstraint("project_id", "path"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    path: str
    size: int
    mtime: float
    hash: str
    lang: Optional[str] = None
    symbols_count: int = 0
    last_indexed_at: Optional[datetime] = None

    project: Optional["Project"] = Relationship(back_populates="file_metas")
