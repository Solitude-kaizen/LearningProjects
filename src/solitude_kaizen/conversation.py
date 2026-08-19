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

def trim_conversation_history(conversation_history, limit=20):
    if len(conversation_history) > limit:
        del conversation_history[:-limit]

    return conversation_history

def create_conversation_message(role, content):
    return {
        "role": role,
        "content": content,
    }

def add_message_to_history(
    conversation_history,
    role,
    content
):
    message = create_conversation_message(
        role,
        content
    )

    conversation_history.append(message)

    return message