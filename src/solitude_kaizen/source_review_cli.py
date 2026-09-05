"""Explicit, one-shot review of pasted material, isolated from personal context."""

from .ai_service import (
    AI_UNAVAILABLE_MESSAGE,
    ProviderError,
    generate_response,
    get_last_provider_used,
    get_provider_info,
)
from .source_review import (
    MAX_EXCERPT_CHARS,
    build_review_prompts,
    format_review,
    parse_review_response,
    validate_review_request,
)


def run_source_review(
    input_function=None,
    print_function=None,
    response_function=None,
    provider_info_function=None,
    provider_used_function=None,
):
    if input_function is None:
        input_function = input
    if print_function is None:
        print_function = print
    if response_function is None:
        response_function = generate_response
    if provider_info_function is None:
        provider_info_function = get_provider_info
    if provider_used_function is None:
        provider_used_function = get_last_provider_used

    def read(prompt):
        value = input_function(prompt)
        if value.strip().casefold() == "/cancel":
            raise EOFError
        return value

    def cancelled():
        print_function("Source review cancelled. Nothing was sent or saved.")
        return {"status": "cancelled", "review": None}

    print_function("--- Optional Source Review ---")
    print_function("Paste only material you are allowed to share. Do not include credentials.")
    print_function("No links are opened. Personal memories and chat context are excluded.")
    print_function("Type /cancel at any prompt to cancel before the request.")
    try:
        title = read("Source title: ")
        url = read("Source HTTP(S) link (optional): ")
        print_function(f"Paste the excerpt (up to {MAX_EXCERPT_CHARS} characters / 100 lines).")
        print_function("Enter /done on a separate line when finished.")
        lines = []
        while True:
            line = read("Excerpt: ")
            if line.strip().casefold() == "/done":
                break
            lines.append(line)
            if len(lines) > 100 or len("\n".join(lines)) > MAX_EXCERPT_CHARS:
                raise ValueError("The excerpt is too long; nothing was sent or saved.")
        question = read("Question about this excerpt: ")
        request = validate_review_request(title, url, "\n".join(lines), question)
        provider_info = provider_info_function()
        print_function("--- Request preview ---")
        print_function("Source:", request["title"])
        print_function("Link (not fetched):", request["url"] or "Not supplied")
        print_function("Excerpt:", request["excerpt"])
        print_function("Question:", request["question"])
        print_function("Configured provider:", provider_info["provider"])
        print_function("Model:", provider_info["model"])
        print_function(
            "Only this material and question will be sent to the configured model. "
            "Cloud use sends them to that provider and may have costs. "
            "Existing provider fallback rules still apply. No review is saved."
        )
        if read("Type 'yes' to request the review, anything else to cancel: ").strip().casefold() != "yes":
            return cancelled()
        system_prompt, user_message = build_review_prompts(request)
    except (EOFError, KeyboardInterrupt):
        return cancelled()
    except ValueError as error:
        print_function("Cannot prepare source review:", str(error))
        return {"status": "invalid", "review": None}
    except ProviderError as error:
        print_function("Could not read provider configuration:", str(error))
        return {"status": "failed", "review": None}

    try:
        response = response_function(system_prompt, user_message)
    except KeyboardInterrupt:
        print_function("Review interrupted. The request may already have reached the provider; nothing was saved.")
        return {"status": "interrupted", "review": None}
    except ProviderError as error:
        print_function("Source review failed:", str(error))
        return {"status": "failed", "review": None}
    if response == AI_UNAVAILABLE_MESSAGE:
        print_function("Source review unavailable. Nothing was saved.")
        return {"status": "failed", "review": None}
    try:
        review = parse_review_response(response, request)
    except ValueError as error:
        print_function("Review not displayed:", str(error))
        print_function("No automatic retry was made. Nothing was saved.")
        return {"status": "invalid_response", "review": None}
    print_function(format_review(request, review))
    provider = provider_used_function()
    if provider:
        print_function("Provider used:", provider)
    return {"status": "completed", "review": review}
