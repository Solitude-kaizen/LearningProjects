import html
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from .database import (
    add_research_item,
    get_research_collection_run_for_date,
    initialize_database,
    record_research_collection_run,
)


RESEARCH_TIMEOUT_SECONDS = 15
RESEARCH_USER_AGENT = (
    "Solitude-Kaizen/2.0 "
    "(+https://github.com/Solitude-Kaizen/LearningProjects)"
)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
HACKER_NEWS_NEW_STORIES_URL = (
    "https://hacker-news.firebaseio.com/v0/newstories.json"
)
HACKER_NEWS_ITEM_URL = (
    "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
)
ARXIV_API_URL = "https://export.arxiv.org/api/query"
YOUTUBE_FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml"
)

YOUTUBE_CHANNELS = (
    (
        "google-developers",
        "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    ),
)

RESEARCH_KEYWORDS = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "llm",
    "language model",
    "agent",
    "ollama",
    "neural",
    "rag",
    "retrieval",
)


class ResearchSourceError(Exception):
    pass


def _get_json(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers={
            "Accept": "application/json",
            "User-Agent": RESEARCH_USER_AGENT,
        },
        timeout=RESEARCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.json()


def _get_text(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers={
            "Accept": "application/atom+xml, application/xml",
            "User-Agent": RESEARCH_USER_AGENT,
        },
        timeout=RESEARCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.text


def _clean_text(value, limit=1000):
    if value is None:
        return ""

    cleaned = " ".join(
        html.unescape(str(value)).split()
    )

    return cleaned[:limit]


def _matches_research_keywords(value):
    lowered_value = _clean_text(value).lower()

    return any(
        re.search(
            rf"\b{re.escape(keyword)}\b",
            lowered_value,
        )
        for keyword in RESEARCH_KEYWORDS
    )


def collect_github_projects():
    try:
        payload = _get_json(
            GITHUB_SEARCH_URL,
            params={
                "q": (
                    "personal assistant memory ollama "
                    "in:name,description,readme language:Python"
                ),
                "sort": "updated",
                "order": "desc",
                "per_page": 5,
            },
        )
    except (requests.RequestException, ValueError) as error:
        raise ResearchSourceError(
            "GitHub could not be reached."
        ) from error

    items = []

    for project in payload.get("items", [])[:5]:
        external_id = project.get("id")
        title = project.get("full_name")
        url = project.get("html_url")

        if not external_id or not title or not url:
            continue

        items.append(
            {
                "source": "github",
                "external_id": str(external_id),
                "title": _clean_text(title, limit=300),
                "url": url,
                "summary": _clean_text(
                    project.get("description"),
                ),
                "published_at": project.get("updated_at"),
            }
        )

    return items


def collect_hacker_news_stories():
    try:
        story_ids = _get_json(
            HACKER_NEWS_NEW_STORIES_URL,
        )
        stories = []

        for story_id in story_ids[:15]:
            story = _get_json(
                HACKER_NEWS_ITEM_URL.format(
                    item_id=story_id,
                )
            )

            if not story:
                continue

            stories.append(story)
    except (requests.RequestException, ValueError, TypeError) as error:
        raise ResearchSourceError(
            "Hacker News could not be reached."
        ) from error

    items = []

    for story in stories:
        title = story.get("title", "")

        if not _matches_research_keywords(title):
            continue

        story_id = story.get("id")

        if not story_id:
            continue

        items.append(
            {
                "source": "hacker-news",
                "external_id": str(story_id),
                "title": _clean_text(title, limit=300),
                "url": story.get("url") or (
                    "https://news.ycombinator.com/item?id="
                    f"{story_id}"
                ),
                "summary": "Public Hacker News story.",
                "published_at": str(story.get("time", "")),
            }
        )

    return items


def collect_arxiv_papers():
    try:
        feed_text = _get_text(
            ARXIV_API_URL,
            params={
                "search_query": (
                    "cat:cs.AI AND "
                    "(all:agent OR all:assistant OR all:memory)"
                ),
                "start": 0,
                "max_results": 5,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )
        root = ET.fromstring(feed_text)
    except (
        requests.RequestException,
        ET.ParseError,
        ValueError,
    ) as error:
        raise ResearchSourceError(
            "arXiv could not be reached."
        ) from error

    atom = "{http://www.w3.org/2005/Atom}"
    items = []

    for entry in root.findall(f"{atom}entry"):
        entry_id = entry.findtext(f"{atom}id")
        title = entry.findtext(f"{atom}title")
        summary = entry.findtext(f"{atom}summary")
        published_at = entry.findtext(f"{atom}published")

        if not entry_id or not title:
            continue

        url = entry_id

        for link in entry.findall(f"{atom}link"):
            if link.attrib.get("rel") == "alternate":
                url = link.attrib.get("href", entry_id)
                break

        items.append(
            {
                "source": "arxiv",
                "external_id": entry_id.rsplit("/", 1)[-1],
                "title": _clean_text(title, limit=300),
                "url": url,
                "summary": _clean_text(summary),
                "published_at": published_at,
            }
        )

    return items


def collect_youtube_videos():
    atom = "{http://www.w3.org/2005/Atom}"
    youtube = "{http://www.youtube.com/xml/schemas/2015}"
    items = []
    successful_channel_count = 0

    for channel_name, channel_id in YOUTUBE_CHANNELS:
        try:
            feed_text = _get_text(
                YOUTUBE_FEED_URL,
                params={"channel_id": channel_id},
            )
            root = ET.fromstring(feed_text)
            successful_channel_count += 1
        except (
            requests.RequestException,
            ET.ParseError,
            ValueError,
        ):
            continue

        for entry in root.findall(f"{atom}entry"):
            video_id = entry.findtext(
                f"{youtube}videoId"
            )
            title = entry.findtext(f"{atom}title")
            published_at = entry.findtext(
                f"{atom}published"
            )

            if (
                not video_id
                or not title
                or not _matches_research_keywords(title)
            ):
                continue

            items.append(
                {
                    "source": f"youtube/{channel_name}",
                    "external_id": video_id,
                    "title": _clean_text(title, limit=300),
                    "url": (
                        "https://www.youtube.com/watch?v="
                        f"{video_id}"
                    ),
                    "summary": (
                        "Public video from the curated "
                        f"{channel_name} channel."
                    ),
                    "published_at": published_at,
                }
            )

    if successful_channel_count == 0:
        raise ResearchSourceError(
            "YouTube feeds could not be reached."
        )

    return items


def collect_public_research(source_functions=None):
    if source_functions is None:
        source_functions = (
            ("github", collect_github_projects),
            ("hacker-news", collect_hacker_news_stories),
            ("arxiv", collect_arxiv_papers),
            ("youtube", collect_youtube_videos),
        )

    items = []
    errors = []

    for source_name, source_function in source_functions:
        try:
            items.extend(source_function())
        except ResearchSourceError as error:
            errors.append(f"{source_name}: {error}")
        except Exception:
            errors.append(
                f"{source_name}: unexpected source error"
            )

    return {
        "items": items,
        "errors": errors,
    }


def is_research_collector_enabled():
    value = os.getenv(
        "SK_RESEARCH_ENABLED",
        "false",
    )

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _normalize_research_item(item):
    source = _clean_text(item.get("source"), limit=100)
    external_id = _clean_text(
        item.get("external_id"),
        limit=300,
    )
    title = _clean_text(item.get("title"), limit=300)
    url = _clean_text(item.get("url"), limit=1000)

    if (
        not source
        or not external_id
        or not title
        or not url.startswith(("https://", "http://"))
    ):
        return None

    return {
        "source": source,
        "external_id": external_id,
        "title": title,
        "url": url,
        "summary": _clean_text(item.get("summary")),
        "published_at": _clean_text(
            item.get("published_at"),
            limit=100,
        ) or None,
    }


def run_research_collection_if_due(
    database_path,
    current_time=None,
    collector_function=None,
):
    initialize_database(database_path)

    if current_time is None:
        current_time = datetime.now().astimezone()

    run_date = current_time.date().isoformat()
    created_at = current_time.isoformat(timespec="seconds")
    existing_run = get_research_collection_run_for_date(
        database_path,
        run_date,
    )

    if existing_run is not None:
        return {
            "status": "skipped",
            "run": existing_run,
        }

    if collector_function is None:
        collector_function = collect_public_research

    try:
        collection = collector_function()
        collected_items = collection.get("items", [])
        errors = list(collection.get("errors", []))
    except Exception:
        collected_items = []
        errors = ["collector: unexpected collection error"]

    new_item_count = 0

    for item in collected_items:
        if not isinstance(item, dict):
            errors.append("collector: invalid research item")
            continue

        normalized_item = _normalize_research_item(item)

        if normalized_item is None:
            errors.append("collector: invalid research item")
            continue

        was_added = add_research_item(
            database_path,
            normalized_item["source"],
            normalized_item["external_id"],
            normalized_item["title"],
            normalized_item["url"],
            normalized_item["summary"],
            normalized_item["published_at"],
            created_at,
        )

        if was_added:
            new_item_count += 1

    if errors and new_item_count:
        status = "partial"
    elif errors:
        status = "failed"
    else:
        status = "completed"

    error_summary = None

    if errors:
        error_summary = "; ".join(errors)[:2000]

    record_research_collection_run(
        database_path,
        run_date,
        status,
        new_item_count,
        created_at,
        error_summary=error_summary,
    )

    collection_run = get_research_collection_run_for_date(
        database_path,
        run_date,
    )

    return {
        "status": status,
        "run": collection_run,
    }


def maybe_run_research_collection(
    database_path,
    current_time=None,
    collector_function=None,
):
    initialize_database(database_path)

    if not is_research_collector_enabled():
        return {
            "status": "disabled",
            "run": None,
        }

    return run_research_collection_if_due(
        database_path,
        current_time=current_time,
        collector_function=collector_function,
    )
