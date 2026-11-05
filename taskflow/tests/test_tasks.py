# tests/test_tasks.py
from taskflow.tasks import add_task, complete_task, list_tasks


def test_add_task_assigns_incremental_ids():
    tasks = []
    t1 = add_task(tasks, "Premiere tache")
    t2 = add_task(tasks, "Deuxieme tache")
    assert t1.id == 1
    assert t2.id == 2
    assert len(tasks) == 2


def test_complete_task_marks_completed_flag():
    tasks = []
    add_task(tasks, "A faire")
    complete_task(tasks, 1)
    assert tasks[0].completed is True


def test_list_tasks_only_pending():
    tasks = []
    add_task(tasks, "Tache 1")
    add_task(tasks, "Tache 2")
    complete_task(tasks, 1)
    pending = list_tasks(tasks, only_pending=True)
    assert len(pending) == 1
    assert pending[0].id == 2
