# core/models.py
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Any, Sequence

@dataclass
class Task:
    id: int
    user_id: int
    title: str
    description: str
    completed: bool
    due_date: Optional[date]

def task_from_row(row: Sequence[Any]) -> "Task":
    """
    Convert a DB row (tuple) to a Task.
    Expected schema: (id, user_id, title, description, completed, due_date, ...)
    """
    id_, user_id, title, desc, completed, due_str = row[:6]
    d = datetime.strptime(due_str, "%Y-%m-%d").date() if due_str else None
    return Task(
        id=int(id_),
        user_id=int(user_id),
        title=str(title or ""),
        description=str(desc or ""),
        completed=bool(completed),
        due_date=d,
    )
