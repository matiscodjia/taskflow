import ollama

QUESTION = "Dans une bibliotheque Python de gestion de tache nommee taskflow, dans quel type de fichier s'attendrait-on a trouver la fonction qui ajoute une tache ?"

response = ollama.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": QUESTION}],
)
print(response["message"]["content"])
