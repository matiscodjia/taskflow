"""Utilitaires de reporting : resume hebdomadaire et export CSV ."""

from datetime import datetime, timedelta
from typing import List

from taskflow.tasks import Task


def weekly_summary(tasks: List[Task]) -> dict:
    """Retourne un resume des taches creees / terminees sur les 7
    derniers jours.
    """
    cutoff = datetime.now() - timedelta(days=7)
    created_this_week = [
        t for t in tasks if datetime.fromisoformat(t.created_at) >= cutoff
    ]
    completed_this_week = [
        t
        for t in tasks
        if t.completed_at and datetime.fromisoformat(t.completed_at) >= cutoff
    ]
    return {
        "created": len(created_this_week),
        "completed": len(completed_this_week),
        "pending": len([t for t in tasks if not t.completed]),
    }


def export_csv(tasks: List[Task], path: str) -> None:
    """Exporte les taches au format CSV (id, title, due_date, completed)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("id,title,due_date,completed\n")
        for task in tasks:
            f.write(f"{task.id},{task.title},{task.due_date or ''},{task.completed}\n")
