import json
from pathlib import Path
from typing import List

from taskflow.tasks import Task


def load_tasks(path: str) -> List[Task]:
    """Charge la liste des taches depuis un fichier JSON.

    Retourne une liste vide si le fichier n'existe pas encore
    """
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Task.from_dict(item) for item in raw]


def save_tasks(path: str, tasks: List[Task]) -> None:
    """Persiste la liste des atches dans un fichier JSON."""
    file_path = Path(path)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=2)
