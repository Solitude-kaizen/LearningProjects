from datetime import datetime

from src.solitude_kaizen.database import (
    get_latest_research_items,
)
from src.solitude_kaizen.research import (
    ResearchSourceError,
    collect_arxiv_papers,
    collect_github_projects,
    collect_hacker_news_stories,
    collect_public_research,
    collect_youtube_videos,
    maybe_run_research_collection,
    run_research_collection_if_due,
)


def make_research_item(
    source="github",
    external_id="123",
    title="Local AI assistant",
):
    return {
        "source": source,
        "external_id": external_id,
        "title": title,
        "url": "https://example.com/research-item",
        "summary": "Public research summary.",
        "published_at": "2026-09-01T09:00:00Z",
    }


def test_collect_github_projects_reads_public_metadata(
    monkeypatch,
):
    def fake_get_json(url, params=None):
        assert "api.github.com" in url
        assert params["per_page"] == 5

        return {
            "items": [
                {
                    "id": 42,
                    "full_name": "example/local-assistant",
                    "html_url": (
                        "https://github.com/example/"
                        "local-assistant"
                    ),
                    "description": "A local memory project.",
                    "updated_at": "2026-09-01T10:00:00Z",
                }
            ]
        }

    monkeypatch.setattr(
        "src.solitude_kaizen.research._get_json",
        fake_get_json,
    )

    items = collect_github_projects()

    assert items == [
        {
            "source": "github",
            "external_id": "42",
            "title": "example/local-assistant",
            "url": (
                "https://github.com/example/local-assistant"
            ),
            "summary": "A local memory project.",
            "published_at": "2026-09-01T10:00:00Z",
        }
    ]


def test_collect_hacker_news_filters_unrelated_stories(
    monkeypatch,
):
    def fake_get_json(url, params=None):
        if url.endswith("newstories.json"):
            return [101, 102]

        if "/101.json" in url:
            return {
                "id": 101,
                "title": "New local AI agent",
                "url": "https://example.com/agent",
                "time": 1788253200,
            }

        return {
            "id": 102,
            "title": "A guide to gardening",
            "url": "https://example.com/garden",
            "time": 1788253201,
        }

    monkeypatch.setattr(
        "src.solitude_kaizen.research._get_json",
        fake_get_json,
    )

    items = collect_hacker_news_stories()

    assert len(items) == 1
    assert items[0]["external_id"] == "101"
    assert items[0]["source"] == "hacker-news"


def test_collect_arxiv_papers_parses_atom_feed(monkeypatch):
    feed = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>https://arxiv.org/abs/2609.00001v1</id>
        <title>Safe Memory for Local Agents</title>
        <summary>Evidence for bounded agent memory.</summary>
        <published>2026-09-01T08:00:00Z</published>
        <link rel="alternate"
              href="https://arxiv.org/abs/2609.00001v1" />
      </entry>
    </feed>
    """

    monkeypatch.setattr(
        "src.solitude_kaizen.research._get_text",
        lambda url, params=None: feed,
    )

    items = collect_arxiv_papers()

    assert len(items) == 1
    assert items[0]["source"] == "arxiv"
    assert items[0]["external_id"] == "2609.00001v1"
    assert items[0]["title"] == "Safe Memory for Local Agents"


def test_collect_youtube_videos_uses_curated_feed(
    monkeypatch,
):
    feed = """
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:yt="http://www.youtube.com/xml/schemas/2015">
      <entry>
        <yt:videoId>video-1</yt:videoId>
        <title>How an AI agent uses memory</title>
        <published>2026-09-01T07:00:00Z</published>
      </entry>
      <entry>
        <yt:videoId>video-2</yt:videoId>
        <title>Developer conference welcome</title>
        <published>2026-09-01T06:00:00Z</published>
      </entry>
    </feed>
    """

    monkeypatch.setattr(
        "src.solitude_kaizen.research._get_text",
        lambda url, params=None: feed,
    )

    items = collect_youtube_videos()

    assert len(items) == 1
    assert items[0]["external_id"] == "video-1"
    assert items[0]["source"] == (
        "youtube/google-developers"
    )


def test_collect_public_research_keeps_successful_sources():
    def successful_source():
        return [make_research_item()]

    def failed_source():
        raise ResearchSourceError("source unavailable")

    result = collect_public_research(
        source_functions=(
            ("working", successful_source),
            ("broken", failed_source),
        )
    )

    assert len(result["items"]) == 1
    assert result["errors"] == [
        "broken: source unavailable"
    ]


def test_research_run_stores_unique_items_and_partial_status(
    tmp_path,
):
    database_path = tmp_path / "solitude_kaizen.db"
    item = make_research_item()

    result = run_research_collection_if_due(
        database_path,
        current_time=datetime(2026, 9, 1, 10, 0, 0),
        collector_function=lambda: {
            "items": [item, item],
            "errors": ["youtube: feed unavailable"],
        },
    )
    stored_items = get_latest_research_items(database_path)

    assert result["status"] == "partial"
    assert result["run"]["new_item_count"] == 1
    assert result["run"]["error_summary"] == (
        "youtube: feed unavailable"
    )
    assert len(stored_items) == 1
    assert stored_items[0]["external_id"] == "123"


def test_research_collection_runs_only_once_per_day(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"
    call_count = {"value": 0}

    def fake_collector():
        call_count["value"] += 1
        return {
            "items": [make_research_item()],
            "errors": [],
        }

    first_result = run_research_collection_if_due(
        database_path,
        current_time=datetime(2026, 9, 1, 10, 0, 0),
        collector_function=fake_collector,
    )
    second_result = run_research_collection_if_due(
        database_path,
        current_time=datetime(2026, 9, 1, 18, 0, 0),
        collector_function=fake_collector,
    )

    assert first_result["status"] == "completed"
    assert second_result["status"] == "skipped"
    assert call_count["value"] == 1


def test_invalid_research_item_records_failed_run(tmp_path):
    database_path = tmp_path / "solitude_kaizen.db"

    result = run_research_collection_if_due(
        database_path,
        current_time=datetime(2026, 9, 1, 10, 0, 0),
        collector_function=lambda: {
            "items": [{"title": "Missing source and link"}],
            "errors": [],
        },
    )

    assert result["status"] == "failed"
    assert result["run"]["new_item_count"] == 0
    assert result["run"]["error_summary"] == (
        "collector: invalid research item"
    )


def test_automatic_research_collection_is_disabled_by_default(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "solitude_kaizen.db"
    monkeypatch.delenv("SK_RESEARCH_ENABLED", raising=False)

    result = maybe_run_research_collection(database_path)

    assert result["status"] == "disabled"
    assert result["run"] is None
