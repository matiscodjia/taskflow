import json

import ollama

response = ollama.generate(
    model="qwen3:8b",
    prompt="Summarize in five points the principles of agentic Summarize",
    think=False,
)

# with open("ollama-server-test.json", "w", encoding="utf-8") as f:
#    f.write(response.model_dump_json(indent=1))

print(response.thinking)
