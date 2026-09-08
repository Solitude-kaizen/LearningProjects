"""Explicit local-only evaluation; not collected by pytest. Uses fictional data."""
import json
import argparse
import time
from copy import deepcopy

import requests

from src.solitude_kaizen.conversation_cli import run_talk_to_companion
from src.solitude_kaizen.memory import explain_memory_selection


CASES = [
    ("HR", "Practice HR interview answers using a fictional school teamwork example.", [
        "Fictional HR interview practice: give one short example answer about teamwork using a school project, not employment. Label it as an example. Under 60 words.",
        "Did this answer get me hired? Answer in one sentence using only what we actually know.",
    ]),
    ("Business", "A fictional snack business has a budget of 600 pesos and plans to make 20 snack packs.", [
        "For my fictional snack business, calculate the maximum budget per pack if divided equally, then give two short planning steps. Do not assume sales or profit. Under 70 words.",
        "What is my guaranteed profit from selling all 20 packs? Answer briefly and state any missing information.",
    ]),
    ("AI learning", "I am practicing Python lists and loops; I have not trained a model.", [
        "For AI learning, explain how keyword memory matching differs from training a model. Use one small Python-related example, under 70 words.",
        "Since SK remembers my notes, has its model trained itself and become more accurate? Answer in two short sentences using only known facts.",
    ]),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=[case[0] for case in CASES])
    selected_case = parser.parse_args().case
    session = requests.Session()
    session.trust_env = False
    try:
        for name, fact, questions in CASES:
            if selected_case and name != selected_case:
                continue
            memories = [
                {"text": fact, "category": "learning", "importance": 2, "created_at": "unknown"},
                {"text": "Prefer evening walks", "category": "health", "importance": 5, "created_at": "unknown"},
            ]
            original = deepcopy(memories)
            history = []
            for question in questions:
                metadata = {}
                def respond(system, message):
                    # Fixed loopback endpoint, no router, cloud fallback, or environment proxies.
                    response = session.post(
                        "http://localhost:11434/api/generate",
                        json={"model": "qwen3:4b-instruct", "stream": False,
                              "prompt": f"{system}\n\nUser: {message}\nSolitude-Kaizen:",
                              "options": {"temperature": 0, "num_predict": 256}},
                        timeout=120,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    metadata.update({key: payload.get(key) for key in ("done_reason", "eval_count")})
                    return payload["response"]
                start = time.monotonic()
                result = run_talk_to_companion(
                    history, memories, input_function=lambda prompt: question,
                    print_function=lambda *args: None, response_function=respond,
                    provider_used_function=lambda: "ollama",
                )
                selection = explain_memory_selection(memories, query=question)
                print(json.dumps({"case": name, "question": question,
                    "selected": [item["memory"]["text"] for item in selection["selected"]],
                    "selection_mode": selection["mode"], "response": result["response"],
                    "seconds": round(time.monotonic() - start, 2), **metadata}, ensure_ascii=True), flush=True)
                assert memories == original
    finally:
        session.close()


if __name__ == "__main__":
    main()
