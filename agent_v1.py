import ollama

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


if __name__ == "__main__":
    print(repondre("Quels fichiers composent le dépôt taskflow?"))
