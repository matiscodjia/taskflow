import os
import subprocess
import sys

REPO_ROOT = "taskflow"


def list_files(sous_dossier: str = "") -> list[str]:
    base = os.path.join(REPO_ROOT, sous_dossier) if sous_dossier else REPO_ROOT
    found = []
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, name), REPO_ROOT)
                found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def read_file(chemin: str) -> str:
    root_abs = os.path.abspath(REPO_ROOT)
    full_path = os.path.abspath(os.path.join(REPO_ROOT, chemin))
    if not full_path.startswith(root_abs + os.sep):
        raise ValueError("Chemin hors du depot autorise")
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def run_tests() -> dict:
    """Execute pytest sur le depot taskflow et retourne le resultat."""
    result = subprocess.run(
        # sys.executable -m pytest : le meme Python que votre agent
        # (evite un "pytest introuvable" ou le pytest d'un autre environnement)
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],  # tronque pour rester raisonnable
        "stderr": result.stderr[-2000:],
    }


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "Liste les fichiers Python (.py) du depot taskflow, de facon recursive. "
                "Renvoie leurs chemins relatifs a la racine du depot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sous_dossier": {
                        "type": "string",
                        "description": (
                            "Sous-dossier du depot a explorer (ex: 'tests'). "
                            "Laisser vide pour lister tout le depot."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit et renvoie le contenu complet d'un fichier du depot taskflow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemin": {
                        "type": "string",
                        "description": (
                            "Chemin du fichier relatif a la racine du depot, "
                            "tel que renvoye par list_files (ex: 'taskflow/tasks.py')."
                        ),
                    },
                },
                "required": ["chemin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": (
                "Execute la suite de tests (pytest) du depot taskflow. Renvoie le code "
                "de retour (0 = tous les tests passent) et la fin des sorties stdout/stderr."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "run_tests": run_tests,
}
