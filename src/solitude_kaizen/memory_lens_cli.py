"""Read-only inspection of the same memory selection used by chat."""

from .memory import explain_memory_selection, format_memory
from .terminal_text import preview_text


def run_memory_lens(memories, input_function=None, print_function=print):
    if input_function is None:
        input_function = input
    print_function("Memory Lens: local preview only; nothing is sent or saved.")
    try:
        query = input_function("Question to inspect (/cancel to leave): ")
    except (EOFError, KeyboardInterrupt):
        query = ""
    if not query.strip() or query.strip().casefold() == "/cancel":
        print_function("Memory preview canceled.")
        return {"status": "canceled"}
    if len(query) > 2000:
        print_function("Please use a question of at most 2000 characters.")
        return {"status": "invalid_query"}

    selection = explain_memory_selection(memories, limit=5, query=query)
    print_function("--- Memory Lens ---")
    print_function("Display note: backslashes and hidden control characters are escaped.")
    print_function("Question keywords:", ", ".join(selection["query_keywords"]) or "none")
    if selection["mode"] == "empty":
        print_function("No saved memories are available.")
    elif selection["mode"] == "fallback":
        print_function("No keyword matches: chat falls back to importance and recency.")
        print_function("These memories may be unrelated to your question.")
    else:
        print_function("Matches ranked by shared-word count, then importance and recency.")
    for entry in selection["selected"]:
        print_function("-", preview_text(format_memory(entry["memory"])))
        print_function("  Shared words:", ", ".join(entry["matched_keywords"]) or "none (fallback)")
    print_function("Selected:", len(selection["selected"]), "of", selection["total_memories"])
    print_function("This explains memory selection, not the model's reasoning or factual accuracy.")
    print_function("Chat can also include recent messages and an explicitly resumed note.")
    print_function("Cloud chat sends its selected context to the provider; this preview does not.")
    return {"status": "previewed", "selection": selection}
