import os
from datetime import datetime

from .ai_service import (
    ProviderError,
    generate_groq_response,
)
from .database import (
    get_kaizen_discovery_for_date,
    initialize_database,
    record_kaizen_discovery,
)


KAIZEN_DISCOVERY_MODEL = "groq/compound-mini"
KAIZEN_DISCOVERY_PROVIDER = "groq"

KAIZEN_SYSTEM_PROMPT = """
You are the read-only research component of Solitude-Kaizen.

Discover one recent, practical improvement relevant to a small,
local-first personal AI assistant. Focus on memory, retrieval,
provider reliability, permissions, evaluation, or resource safety.

Requirements:
- Use current public web sources.
- Include direct source links.
- Separate evidence from your recommendation.
- Prefer a small, testable improvement over a large framework.
- Do not request or infer private user information.
- Do not modify code, install software, or perform external actions.
""".strip()

KAIZEN_PUBLIC_PROJECT_DESCRIPTION = """
Solitude-Kaizen is a Python personal AI learning project with a CLI,
SQLite memory work in progress, replaceable Groq/OpenAI/Ollama
providers, structured provider errors, and local fallback. Suggest
one improvement for human review. Do not assume access to private
memories, files, credentials, or system information.
""".strip()


def is_daily_kaizen_enabled():
    value = os.getenv(
        "KAIZEN_DISCOVERY_ENABLED",
        "false",
    )

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def generate_daily_discovery():
    return generate_groq_response(
        KAIZEN_SYSTEM_PROMPT,
        KAIZEN_PUBLIC_PROJECT_DESCRIPTION,
        model=KAIZEN_DISCOVERY_MODEL,
    )


def run_daily_kaizen_if_due(
    database_path,
    current_time=None,
    discovery_function=None,
):
    initialize_database(database_path)

    if current_time is None:
        current_time = datetime.now().astimezone()

    run_date = current_time.date().isoformat()
    created_at = current_time.isoformat(timespec="seconds")

    existing_discovery = get_kaizen_discovery_for_date(
        database_path,
        run_date,
    )

    if existing_discovery is not None:
        return {
            "status": "skipped",
            "discovery": existing_discovery,
        }

    if discovery_function is None:
        discovery_function = generate_daily_discovery

    try:
        report = discovery_function()
        status = "completed"
        error_kind = None
    except ProviderError as error:
        report = str(error)
        status = "failed"
        error_kind = error.kind

    record_kaizen_discovery(
        database_path,
        run_date,
        status,
        report,
        KAIZEN_DISCOVERY_PROVIDER,
        created_at,
        error_kind=error_kind,
    )

    discovery = get_kaizen_discovery_for_date(
        database_path,
        run_date,
    )

    return {
        "status": status,
        "discovery": discovery,
    }


def maybe_run_daily_kaizen(
    database_path,
    current_time=None,
    discovery_function=None,
):
    initialize_database(database_path)

    if not is_daily_kaizen_enabled():
        return {
            "status": "disabled",
            "discovery": None,
        }

    return run_daily_kaizen_if_due(
        database_path,
        current_time=current_time,
        discovery_function=discovery_function,
    )
