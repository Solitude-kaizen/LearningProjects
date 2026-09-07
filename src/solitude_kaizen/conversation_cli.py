from .ai_service import (
    AI_UNAVAILABLE_MESSAGE,
    ProviderError,
    generate_response,
    get_last_provider_used,
    get_provider_info,
)
from .conversation import (
    add_message_to_history,
    build_conversation_context,
    record_assistant_response,
)
from .memory import build_memory_context
from .prompt import build_system_prompt
from .session_notes import format_session_note
from .terminal_text import preview_text


def run_talk_to_companion(
    conversation_history,
    memories,
    input_function=None,
    print_function=print,
    response_function=generate_response,
    provider_used_function=get_last_provider_used,
    session_note=None,
    review_before_send=False,
    provider_info_function=None,
):
    if input_function is None:
        input_function = input
    try:
        user_message = input_function("You: ")
    except (EOFError, KeyboardInterrupt):
        user_message = ""

    if not user_message.strip():
        print_function()
        print_function("Chat cancelled. No message was sent.")
        return {
            "status": "cancelled",
            "error": None,
            "response": None,
            "provider": None,
        }

    conversation_context = build_conversation_context(
        conversation_history,
        limit=6,
    )
    memory_context = build_memory_context(
        memories,
        limit=5,
        query=user_message,
    )
    system_prompt = build_system_prompt(
        memory_context,
        conversation_context,
        session_note_context=format_session_note(session_note) if session_note else "",
    )

    if review_before_send:
        if provider_info_function is None:
            provider_info_function = get_provider_info
        try:
            provider_info = provider_info_function()
        except ProviderError as error:
            print_function("Could not prepare chat preview:", str(error))
            return {"status": "failed", "error": error, "response": None, "provider": None}
        print_function("--- Review Before Send ---")
        print_function("Configured provider:", provider_info["provider"])
        print_function("Model:", provider_info["model"])
        print_function("Display note: backslashes and hidden control characters are escaped; original text is sent.")
        print_function("Application system prompt:")
        print_function(preview_text(system_prompt))
        print_function("Your message:")
        print_function(preview_text(user_message))
        print_function(
            "These are the application texts to send. Provider wrappers may add formatting. "
            "Cloud requests share this context with the provider and may cost money. "
            "Existing fallback rules apply. Nothing has been sent yet."
        )
        try:
            confirmation = input_function("Type 'yes' to send, anything else to cancel: ")
        except (EOFError, KeyboardInterrupt):
            confirmation = ""
        if confirmation.strip().casefold() != "yes":
            print_function("Chat cancelled. No message was sent.")
            return {"status": "cancelled", "error": None, "response": None, "provider": None}

    add_message_to_history(conversation_history, "user", user_message)

    try:
        response = response_function(
            system_prompt,
            user_message,
        )
    except KeyboardInterrupt:
        conversation_history.pop()
        print_function()
        print_function(
            "Chat interrupted. The request may already have reached the provider. "
            "The unanswered turn was removed from this session; SK will not resubmit it."
        )
        return {
            "status": "interrupted",
            "error": None,
            "response": None,
            "provider": None,
        }
    except ProviderError as error:
        conversation_history.pop()
        print_function()
        print_function("Solitude-Kaizen:")
        print_function(str(error))
        print_function(
            f"Diagnostic: {error.provider}/{error.kind}"
        )

        return {
            "status": "failed",
            "error": error,
            "response": None,
            "provider": None,
        }

    if not isinstance(response, str) or not response.strip():
        conversation_history.pop()
        print_function("The provider returned no usable text. The unanswered turn was not kept.")
        return {
            "status": "invalid_response",
            "error": None,
            "response": None,
            "provider": None,
        }

    if response == AI_UNAVAILABLE_MESSAGE:
        conversation_history.pop()
        print_function(AI_UNAVAILABLE_MESSAGE)
        print_function("The unanswered turn was not kept in conversation history.")
        return {
            "status": "failed",
            "error": None,
            "response": None,
            "provider": None,
        }

    print_function()
    print_function("Solitude-Kaizen:")
    print_function(response)
    record_assistant_response(
        conversation_history,
        response,
        limit=20,
    )
    provider_used = provider_used_function()

    if provider_used:
        print_function("[Provider:", provider_used + "]")

    return {
        "status": "completed",
        "error": None,
        "response": response,
        "provider": provider_used,
    }


def run_view_ai_provider(
    print_function=print,
    provider_info_function=get_provider_info,
):
    try:
        provider_info = provider_info_function()
    except ProviderError as error:
        print_function()
        print_function("Could not read AI provider configuration.")
        print_function(
            f"Diagnostic: {error.provider}/{error.kind}"
        )

        return {
            "status": "failed",
            "error": error,
            "provider_info": None,
        }

    print_function()
    print_function("--- AI Provider ---")
    print_function("Active provider:", provider_info["provider"])
    print_function("Model:", provider_info["model"])
    print_function("Type:", provider_info["type"])

    return {
        "status": "available",
        "error": None,
        "provider_info": provider_info,
    }


def run_clear_conversation(
    conversation_history,
    print_function=print,
    input_function=None,
    has_session_note=False,
):
    if input_function is None:
        input_function = input

    message_count = len(conversation_history)
    print_function()

    if message_count == 0 and not has_session_note:
        print_function("Conversation history is already empty.")
        return {"status": "empty", "message_count": 0}

    print_function("--- Clear Conversation Preview ---")
    print_function("Messages to clear:", message_count)
    print_function("Only this session's chat will be cleared; saved memories stay.")
    if has_session_note:
        print_function("The resumed note will also be detached; its saved copy stays.")
    print_function("This cannot be undone within this session.")

    try:
        confirmation = input_function(
            "Type 'yes' to confirm, anything else to cancel: "
        )
    except (EOFError, KeyboardInterrupt):
        confirmation = ""

    if confirmation.strip().lower() != "yes":
        print_function("Cancelled. Conversation history was not changed.")
        return {"status": "cancelled", "message_count": message_count}

    conversation_history.clear()
    print_function("Conversation history cleared.")

    return {
        "status": "cleared",
        "message_count": 0,
    }


def run_view_conversation_status(
    conversation_history,
    print_function=print,
):
    message_count = len(conversation_history)
    print_function()
    print_function("--- Conversation Status ---")
    print_function(
        "Messages in short-term history:",
        message_count,
    )

    return {
        "status": "available",
        "message_count": message_count,
    }
