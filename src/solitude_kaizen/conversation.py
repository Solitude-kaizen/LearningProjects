def build_conversation_context(conversation_history, limit=6):
    recent_messages = conversation_history[-limit:]

    lines = []

    for message in recent_messages:
        role = message["role"]
        content = message["content"]

        lines.append(
            f"{role.title()}: {content}"
        )

    return "\n".join(lines)