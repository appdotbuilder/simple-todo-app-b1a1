from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


# Persistent models (stored in database)
class Task(SQLModel, table=True):
    __tablename__ = "tasks"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class TaskCreate(SQLModel, table=False):
    title: str = Field(max_length=200)


class TaskUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=200)
    completed: Optional[bool] = Field(default=None)
