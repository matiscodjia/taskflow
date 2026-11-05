"""Modele de tache et operations de base."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Task:
    id: int
    title: str
    created_at: str
    due_date: Optional[str] = None
    completed: bool = False
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(**data)


def _next_id(tasks: List[Task]) -> int:
    if not tasks:
        return 1
    return max(task.id for task in tasks) + 1


def add_task(tasks: List[Task], title: str, due_date: Optional[str] = None) -> Task:
    new_task = Task(
        id=_next_id(tasks),
        title=title,
        created_at=datetime.now().isoformat(timespec="seconds"),
        due_date=due_date,
    )
    tasks.append(new_task)
    return new_task


# Il n'y a pas dans le sujet le completed at dans la fonction compelete_task
def complete_task(tasks: List[Task], task_id: int) -> Task:
    """Marque une tache comme terminee."""
    for task in tasks:
        if task.id == task_id:
            task.completed = True
            return task
    raise ValueError(f"Aucune tache avec l'id {task_id}")


def list_tasks(tasks: List[Task], only_pending: bool = False) -> List[Task]:
    """Retourne la liste des taches, filtree sur les taches en cours si demande."""
    if only_pending:
        return [t for t in tasks if not t.completed]
    return list(tasks)
