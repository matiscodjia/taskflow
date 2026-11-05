# fil_rouge_s1.py
"""Livrable S1 : agent de diagnostic de tickets sur le depot taskflow.

Rassemble les etapes 7 (outils + tool calling) et 8 (sortie structuree) :
- trois outils : list_files, read_file, run_tests ;
- une boucle d'appels d'outils bornee (MAX_ITERATIONS) ;
- une sortie finale DiagnosticTicket validee par pydantic, avec re-prompt
  puis echec explicite en cas de JSON invalide.

Usage (depuis le dossier qui CONTIENT taskflow/) :
    uv run fil_rouge_s1.py            # ticket 1 de taskflow/tickets.md
    uv run fil_rouge_s1.py 3          # ticket 3
    uv run fil_rouge_s1.py "Quelle fonction gere l'ajout d'une tache ?"

Le diagnostic (JSON) sort sur stdout, la trace des appels d'outils sur stderr.
"""

import json
import os
import re
import subprocess
import sys
from typing import Literal

import ollama
from pydantic import BaseModel, Field, ValidationError

MODEL = "qwen3:8b"

MAX_ITERATIONS = 6

REPO_ROOT = "taskflow"


# --- Etape 7 : les outils ------------------------------------------------------


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


# --- Etape 7 : l'agent et sa boucle d'appels d'outils --------------------------

SYSTEM_PROMPT = """Tu es un assistant qui aide a comprendre et maintenir un projet logiciel.
Les questions portent sur ce projet : son code, son fonctionnement, sa structure.

Tu disposes d'outils qui te donnent acces au projet. Tu ne connais pas son contenu
a l'avance : appuie-toi sur ces outils pour aller chercher l'information dont tu as
besoin avant de repondre, et n'hesite pas a les enchainer.

Quand la question mentionne un element precis (fonction, classe, fichier) et que tu
ne l'as pas encore trouve, continue a explorer les autres fichiers plausibles :
ne pas l'avoir vu dans un fichier ne prouve pas qu'il n'existe pas. Ne conclus a
son absence qu'apres avoir examine tous les fichiers susceptibles de le contenir.

Fonde ta reponse uniquement sur ce que tu as observe et cite tes sources
(fichiers, fonctions). Si l'information est introuvable, dis-le clairement
plutot que de la deviner."""


def repondre(question: str) -> str:
    contexte = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    for _ in range(MAX_ITERATIONS):
        response = ollama.chat(model=MODEL, messages=contexte, tools=TOOLS_SCHEMA)
        contexte.append(response["message"])
        tool_calls = response["message"].get("tool_calls") or []
        # Boucle d'appel aux tools
        for call in tool_calls:
            # Trace sur stderr : stdout reste reserve au diagnostic JSON
            print(f"[outil] {call.function.name}({call.function.arguments})", file=sys.stderr)
            try:
                fn = AVAILABLE_FUNCTIONS[call.function.name]
            except KeyError as e:
                contexte.append(
                    {
                        "role": "tool",
                        "content": f"Erreur : outil {call.function.name} inconnu. Outils disponibles : {AVAILABLE_FUNCTIONS.keys()}",
                        "tool_name": call.function.name,
                    }
                )
                continue
            try:
                result = fn(**call.function.arguments)
            except Exception as e:
                contexte.append(
                    {
                        "role": "tool",
                        "content": f"Erreur {type(e).__name__} : {e}",
                        "tool_name": call.function.name,
                    }
                )
                continue
            contexte.append(
                {
                    "role": "tool",
                    "content": str(result),
                    "tool_name": call.function.name,
                }
            )
        if not tool_calls:
            return response["message"]["content"]
    return "Echec de la boucle agentique"


# --- Etape 8.2 : sortie finale contrainte --------------------------------------


class DiagnosticTicket(BaseModel):
    fichiers_concernes: list[str]
    cause_probable: str
    correctif_propose: str | None = None
    confiance: float = Field(ge=0.0, le=1.0)
    statut: Literal["diagnostique", "information_insuffisante"]


# --- Etape 8.3 : validation et gestion explicite de l'echec --------------------


def diagnostiquer(prompt_final: str, tentatives: int = 1) -> DiagnosticTicket:
    for i in range(tentatives + 1):
        # Sortie structuree native d'Ollama : le schema JSON contraint la generation
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt_final}],
            format=DiagnosticTicket.model_json_schema(),
        )
        brut = response["message"]["content"]
        try:
            return DiagnosticTicket.model_validate_json(brut)
        except ValidationError as e:
            if i == tentatives:
                raise RuntimeError(
                    "Le modele n'a pas produit de JSON conforme "
                    f"apres {tentatives + 1} tentatives : {e}"
                ) from e
            prompt_final += (
                "\n\nTa reponse precedente etait invalide :\n"
                + str(e)
                + "\nCorrige et renvoie uniquement un JSON conforme au schema."
            )


def traiter_ticket(ticket: str) -> DiagnosticTicket:
    # 1. L'agent explore le projet avec ses outils (lecture du code, tests)
    analyse = repondre(
        "Voici un ticket utilisateur sur le projet. Explore le code (et lance les "
        f"tests si c'est utile) pour en trouver la cause.\n\n{ticket}"
    )
    # 2. Prompt final : on demande UNIQUEMENT un JSON conforme au schema
    prompt_final = (
        f"Ticket :\n{ticket}\n\n"
        f"Analyse realisee en explorant le code :\n{analyse}\n\n"
        "A partir de cette analyse, produis le diagnostic du ticket. "
        "Reponds UNIQUEMENT avec un JSON conforme a ce schema, sans texte autour :\n"
        f"{json.dumps(DiagnosticTicket.model_json_schema(), ensure_ascii=False)}\n\n"
        "Si la demande est ambigue ou si l'analyse ne permet pas de conclure, "
        "utilise le statut 'information_insuffisante' avec une confiance basse."
    )
    return diagnostiquer(prompt_final)


# --- Point d'entree --------------------------------------------------------------


def charger_ticket(numero: int) -> str:
    """Extrait le ticket n de taskflow/tickets.md (sections '# Ticket n ...')."""
    with open(os.path.join(REPO_ROOT, "tickets.md"), encoding="utf-8") as f:
        sections = re.split(r"^# Ticket (\d+).*$", f.read(), flags=re.MULTILINE)
    # re.split avec un groupe : ["", "1", contenu1, "2", contenu2, ...]
    tickets = {int(n): contenu.strip() for n, contenu in zip(sections[1::2], sections[2::2])}
    if numero not in tickets:
        raise SystemExit(f"Ticket {numero} introuvable (disponibles : {sorted(tickets)})")
    # Retire les "(Note : ...)" destinees aux etudiants : elles donneraient la reponse a l'agent
    return re.sub(r"\(Note :.*?\)\s*$", "", tickets[numero], flags=re.DOTALL).strip()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    demande = charger_ticket(int(arg)) if arg.isdigit() else arg
    try:
        print(traiter_ticket(demande).model_dump_json(indent=2))
    except RuntimeError as e:
        # Echec explicite : jamais de sortie silencieusement invalide
        print(f"ECHEC : {e}", file=sys.stderr)
        sys.exit(1)
