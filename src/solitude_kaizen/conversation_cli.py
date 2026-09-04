from .ai_service import (
    ProviderError,
    generate_response,
    get_last_provider_used,
    get_provider_info,
)
from .conversation import (
    prepare_user_turn,
    record_assistant_response,
)
from .memory import build_memory_context
from .prompt import build_system_prompt


def run_talk_to_companion(
    conversation_history,
    memories,
    input_function=input,
    print_function=print,
    response_function=generate_response,
    provider_used_function=get_last_provider_used,
):
    user_message = input_function("You: ")
    conversation_context = prepare_user_turn(
        conversation_history,
        user_message,
        context_limit=6,
    )
    memory_context = build_memory_context(
        memories,
        limit=5,
        query=user_message,
    )
    system_prompt = build_system_prompt(
        memory_context,
        conversation_context,
    )

    try:
        response = response_function(
            system_prompt,
            user_message,
        )
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
):
    conversation_history.clear()
    print_function()
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
