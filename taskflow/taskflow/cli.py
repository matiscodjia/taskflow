"""Interface en ligne de commande de taskflow."""

import argparse

from taskflow.reports import export_csv, weekly_summary
from taskflow.storage import load_tasks, save_tasks
from taskflow.tasks import add_task, complete_task, list_tasks

DEFAULT_DB = "tasks.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskflow")
    parser.add_argument(
        "--db", default=DEFAULT_DB, help="Chemin du fichier de stockage JSON"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Ajouter une tache")
    add_parser.add_argument("title")
    add_parser.add_argument("--due", default=None)

    complete_parser = subparsers.add_parser(
        "complete", help="Marquer une tache comme terminee"
    )
    complete_parser.add_argument("task_id", type=int)

    list_parser = subparsers.add_parser("list", help="Lister les taches")
    list_parser.add_argument("--pending-only", action="store_true")

    subparsers.add_parser("report", help="Afficher le resume hebdomadaire")

    export_parser = subparsers.add_parser("export", help="Exporter les taches en CSV")
    export_parser.add_argument("csv_path")

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    tasks = load_tasks(args.db)

    if args.command == "add":
        task = add_task(tasks, args.title, due_date=args.due)
        print(f"Tache #{task.id} ajoutee : {task.title}")
    elif args.command == "complete":
        task = complete_task(tasks, args.task_id)
        print(f"Tache #{task.id} marquee terminee")
    elif args.command == "list":
        for task in list_tasks(tasks, only_pending=args.pending_only):
            state = "faite" if task.completed else "en cours"
            print(f"#{task.id} [{state}] {task.title}")
    elif args.command == "report":
        print(weekly_summary(tasks))
    elif args.command == "export":
        export_csv(tasks, args.csv_path)
        print(f"Export ecrit dans {args.csv_path}")

    save_tasks(args.db, tasks)


if __name__ == "__main__":
    main()
