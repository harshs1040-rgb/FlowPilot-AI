from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class WorkflowHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    objective: str
    status: str = "completed"

    result_json: str

    created_at: datetime = Field(default_factory=datetime.utcnow)