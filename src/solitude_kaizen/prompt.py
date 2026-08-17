def build_system_prompt(memory_context):
    return (
        "You are Solitude-Kaizen, a personal AI assistant.\n\n"
        "Use the following remembered information when it is "
        "relevant to the conversation.\n"
        "Do not force memories into responses when they are not relevant.\n\n"
        "Relevant memories:\n"
        f"{memory_context}"
    )