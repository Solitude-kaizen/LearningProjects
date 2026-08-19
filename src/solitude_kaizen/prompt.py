def build_system_prompt(memory_context, conversation_context=""):
    prompt = (
        "You are Solitude-Kaizen, a personal AI assistant.\n\n"
        "Use the following remembered information when it is "
        "relevant to the conversation.\n"
        "Do not force memories into responses when they are not relevant.\n\n"
        "Relevant memories:\n"
        f"{memory_context}"
    )

    if conversation_context:
        prompt += (
            "\n\nRecent conversation:\n"
            f"{conversation_context}"
        )

    return prompt