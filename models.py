from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class Assignment(BaseModel):
    id: Optional[int] = Field(default=None, description="Unique identifier for the assignment")
    title: str = Field(..., description="Title of the assignment")
    course: str = Field(..., description="Course name (e.g., Math, Physics)")
    description: str = Field(default="", description="Detailed description of the task")
    due_date: str = Field(..., description="Due date in YYYY-MM-DD format")
    priority: str = Field(..., description="Priority level: High, Medium, or Low")
    status: str = Field(default="Pending", description="Current status: Pending or Completed")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = ["High", "Medium", "Low"]
        if v not in allowed:
            raise ValueError(f"Priority must be one of {allowed}")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("due_date must be in YYYY-MM-DD format")