from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    kind: str
    content: Optional[str] = None
    uri: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
