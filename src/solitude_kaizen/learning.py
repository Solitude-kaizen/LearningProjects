import re
from datetime import datetime

from .database import (
    complete_learning_lesson,
    get_current_learning_lesson,
    get_learning_lesson_by_id,
    get_learning_progress,
    get_unstudied_research_items,
    initialize_database,
    record_learning_lesson,
)


LEARNING_PURPOSE = (
    "Learn continuously so Solitude-Kaizen and its creator can grow "
    "together, truthfully, safely, and one small step at a time."
)

RELEVANCE_PATTERNS = (
    (r"\bmemory\b", 6),
    (r"\bretrieval\b", 5),
    (r"\blocal\b", 4),
    (r"\bollama\b", 5),
    (r"\bprivacy\b", 5),
    (r"\bsafety\b", 5),
    (r"\bevaluation\b", 4),
    (r"\bpermission", 4),
    (r"\bassistant\b", 3),
    (r"\bagent", 3),
    (r"\bllm\b", 2),
    (r"\blanguage model", 2),
)


def _clean_text(value, limit):
    return " ".join(str(value or "").split())[:limit]


def _source_score(source):
    if source == "arxiv":
        return 4

    if source == "github":
        return 3

    if source.startswith("youtube/"):
        return 2

    if source == "hacker-news":
        return 1

    return 0


def score_research_item(item):
    text = _clean_text(
        f"{item.get('title', '')} {item.get('summary', '')}",
        limit=1500,
    ).lower()
    score = _source_score(item.get("source", ""))

    for pattern, weight in RELEVANCE_PATTERNS:
        if re.search(pattern, text):
            score += weight

    return score


def select_research_item(research_items):
    if not research_items:
        return None

    return max(research_items, key=score_research_item)


def _find_focus(item):
    text = _clean_text(
        f"{item.get('title', '')} {item.get('summary', '')}",
        limit=1500,
    ).lower()

    focus_options = (
        (r"\bmemory\b|\bretrieval\b", "memory and retrieval"),
        (r"\bprivacy\b|\bsafety\b|\bpermission", "safety"),
        (r"\blocal\b|\bollama\b", "local AI independence"),
        (r"\bevaluation\b|\bbenchmark", "evaluation"),
        (r"\bagent|\bassistant\b", "assistant behavior"),
    )

    for pattern, focus in focus_options:
        if re.search(pattern, text):
            return focus

    return "personal AI design"


def _build_baby_step(source):
    if source == "arxiv":
        return (
            "Spend 10 minutes reading only the abstract and conclusion. "
            "Write down one supported claim and one limitation."
        )

    if source == "github":
        return (
            "Spend 10 minutes reading the project README. Identify one "
            "useful idea, one dependency, and one safety trade-off. Do "
            "not install or run the project yet."
        )

    if source == "hacker-news":
        return (
            "Spend 10 minutes opening the original link. Write down one "
            "claim, then check whether the page provides primary evidence."
        )

    if source.startswith("youtube/"):
        return (
            "Watch no more than 10 minutes. Pause and write down one "
            "concept plus one question you still have."
        )

    return (
        "Spend 10 minutes reviewing the source. Write down one useful "
        "idea and one reason it may not apply to SK."
    )


def build_learning_lesson(item):
    title = _clean_text(item.get("title"), limit=300)
    source = _clean_text(item.get("source"), limit=100)
    summary = _clean_text(item.get("summary"), limit=1000)

    if not title or not source:
        raise ValueError("Research item needs a title and source.")

    focus = _find_focus(item)

    if summary:
        evidence_summary = (
            "Unreviewed public metadata: " + summary
        )
    else:
        evidence_summary = (
            "Unreviewed public metadata has no summary. Read the source "
            "before drawing a conclusion."
        )

    return {
        "topic": title,
        "why_it_matters": (
            f"This may help SK understand {focus}. The source has not "
            "been verified, so it is a question to investigate rather "
            "than knowledge to trust."
        ),
        "evidence_summary": evidence_summary,
        "baby_step": _build_baby_step(source),
        "reflection_question": (
            "What did you learn, what evidence supports it, and what "
            "remains uncertain?"
        ),
        "improvement_proposal": (
            f"Human-review proposal: compare the approach in '{title}' "
            f"with SK's current {focus}. If the evidence is useful, "
            "define one expected benefit, one risk, and one reversible "
            "test before changing any code."
        ),
    }


def create_next_learning_lesson(database_path, current_time=None):
    initialize_database(database_path)

    current_lesson = get_current_learning_lesson(database_path)

    if current_lesson is not None:
        return {
            "status": "existing",
            "lesson": current_lesson,
        }

    research_items = get_unstudied_research_items(database_path)
    selected_item = select_research_item(research_items)

    if selected_item is None:
        return {
            "status": "no_research",
            "lesson": None,
        }

    if current_time is None:
        current_time = datetime.now().astimezone()

    content = build_learning_lesson(selected_item)
    lesson_id = record_learning_lesson(
        database_path,
        selected_item["id"],
        content["topic"],
        content["why_it_matters"],
        content["evidence_summary"],
        content["baby_step"],
        content["reflection_question"],
        content["improvement_proposal"],
        current_time.isoformat(timespec="seconds"),
    )

    return {
        "status": "created",
        "lesson": get_learning_lesson_by_id(
            database_path,
            lesson_id,
        ),
    }


def get_active_learning_lesson(database_path):
    initialize_database(database_path)

    return get_current_learning_lesson(database_path)


def finish_active_learning_lesson(
    database_path,
    reflection,
    current_time=None,
):
    initialize_database(database_path)

    current_lesson = get_current_learning_lesson(database_path)

    if current_lesson is None:
        return {
            "status": "no_lesson",
            "lesson": None,
        }

    cleaned_reflection = _clean_text(reflection, limit=2001)

    if not cleaned_reflection:
        raise ValueError("A short reflection is required.")

    if len(cleaned_reflection) > 2000:
        raise ValueError("Please keep the reflection under 2,000 characters.")

    if current_time is None:
        current_time = datetime.now().astimezone()

    completed = complete_learning_lesson(
        database_path,
        current_lesson["id"],
        cleaned_reflection,
        current_time.isoformat(timespec="seconds"),
    )

    if not completed:
        return {
            "status": "not_completed",
            "lesson": current_lesson,
        }

    return {
        "status": "completed",
        "lesson": get_learning_lesson_by_id(
            database_path,
            current_lesson["id"],
        ),
    }


def read_learning_progress(database_path):
    initialize_database(database_path)

    return get_learning_progress(database_path)
