import json
from typing import Literal

import ollama
from pydantic import BaseModel, Field, ValidationError

from tools import AVAILABLE_FUNCTIONS, TOOLS_SCHEMA

MODEL = "qwen3:8b"

MAX_ITERATIONS = 6

SYSTEM_PROMPT = """Tu es un assistant qui aide a comprendre et maintenir un projet logiciel.
Les questions portent sur ce projet : son code, son fonctionnement, sa structure.

Tu disposes d'outils qui te donnent acces au projet. Tu ne connais pas son contenu
a l'avance : appuie-toi sur ces outils pour aller chercher l'information dont tu as
besoin avant de repondre, et n'hesite pas a les enchainer.

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


# --- 8.2 : sortie finale contrainte -------------------------------------------


class DiagnosticTicket(BaseModel):
    fichiers_concernes: list[str]
    cause_probable: str
    correctif_propose: str | None = None
    confiance: float = Field(ge=0.0, le=1.0)
    statut: Literal["diagnostique", "information_insuffisante"]


# --- 8.3 : validation et gestion explicite de l'echec -------------------------


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


if __name__ == "__main__":
    TICKET = """Titre : "complete_task ne met pas a jour la date de completion"
Description : Quand j'appelle `complete_task`, la tache passe bien a "terminee"
mais je ne retrouve jamais quand elle a ete terminee. Le rapport hebdomadaire
semble aussi ne jamais compter de taches completees recemment."""
    print(traiter_ticket(TICKET).model_dump_json(indent=2))
