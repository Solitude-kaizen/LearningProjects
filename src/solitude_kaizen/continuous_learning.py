import os
from datetime import datetime

from .kaizen import maybe_run_daily_kaizen
from .learning import create_daily_learning_lesson_if_due
from .research import maybe_run_research_collection


def is_continuous_learning_enabled():
    value = os.getenv(
        "SK_CONTINUOUS_LEARNING_ENABLED",
        "false",
    )

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _summarize_cycle(research, kaizen, lesson):
    if research["status"] in {"partial", "failed"}:
        return "attention"

    if kaizen["status"] == "failed":
        return "attention"

    if lesson["status"] == "created":
        return "lesson_created"

    if lesson["status"] == "existing":
        return "waiting_for_reflection"

    if lesson["status"] == "no_research":
        return "waiting_for_research"

    if lesson["status"] == "skipped_daily_limit":
        return "daily_limit_reached"

    if (
        research["status"] == "completed"
        or kaizen["status"] == "completed"
    ):
        return "updated"

    if all(
        result["status"] == "disabled"
        for result in (research, kaizen, lesson)
    ):
        return "disabled"

    return "idle"


def run_companion_startup(
    database_path,
    current_time=None,
    research_function=None,
    kaizen_function=None,
):
    """Run permitted research checks without preparing study lessons."""
    if current_time is None:
        current_time = datetime.now().astimezone()

    if research_function is None:
        research_function = maybe_run_research_collection

    if kaizen_function is None:
        kaizen_function = maybe_run_daily_kaizen

    research = research_function(
        database_path,
        current_time=current_time,
    )
    kaizen = kaizen_function(
        database_path,
        current_time=current_time,
    )

    return {
        "status": _summarize_cycle(
            research,
            kaizen,
            {"status": "disabled"},
        ),
        "research": research,
        "kaizen": kaizen,
        "ran_at": current_time.isoformat(timespec="seconds"),
    }


def run_controlled_learning_cycle(
    database_path,
    current_time=None,
    research_function=None,
    kaizen_function=None,
    lesson_function=None,
):
    """Retain the legacy opt-in study cycle for explicit callers only."""
    if current_time is None:
        current_time = datetime.now().astimezone()

    startup = run_companion_startup(
        database_path,
        current_time=current_time,
        research_function=research_function,
        kaizen_function=kaizen_function,
    )

    if lesson_function is None:
        lesson_function = create_daily_learning_lesson_if_due

    if is_continuous_learning_enabled():
        lesson = lesson_function(
            database_path,
            current_time=current_time,
        )
    else:
        lesson = {
            "status": "disabled",
            "lesson": None,
        }

    return {
        **startup,
        "status": _summarize_cycle(
            startup["research"],
            startup["kaizen"],
            lesson,
        ),
        "lesson": lesson,
    }
