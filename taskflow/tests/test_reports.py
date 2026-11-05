# tests/test_reports.py
from taskflow.tasks import add_task, complete_task
from taskflow.reports import export_csv, weekly_summary


def test_weekly_summary_counts_pending():
    tasks = []
    add_task(tasks, "Tache 1")
    add_task(tasks, "Tache 2")
    complete_task(tasks, 1)
    summary = weekly_summary(tasks)
    assert summary["pending"] == 1


def test_export_csv_format(tmp_path):
    tasks = []
    add_task(tasks, "Tache simple", due_date="2026-12-01")
    chemin = tmp_path / "export.csv"
    export_csv(tasks, str(chemin))
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    assert lignes[0] == "id,title,due_date,completed"
    assert lignes[1] == "1,Tache simple,2026-12-01,False"
