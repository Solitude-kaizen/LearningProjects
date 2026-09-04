from .database import (
    get_latest_kaizen_discovery,
    get_latest_research_items,
)
from .research import run_research_collection_if_due
from .research_labels import describe_research_source


def run_view_latest_kaizen_discovery(
    database_path,
    print_function=print,
):
    discovery = get_latest_kaizen_discovery(database_path)

    print_function()
    print_function("--- Latest Kaizen Discovery ---")

    if discovery is None:
        print_function("No Kaizen discovery is available yet.")

        return None

    print_function("Date:", discovery["run_date"])
    print_function("Status:", discovery["status"])
    print_function("Provider:", discovery["provider"])

    if discovery["error_kind"]:
        print_function("Diagnostic:", discovery["error_kind"])

    print_function()
    print_function(discovery["report"])

    return discovery


def run_collect_public_research(
    database_path,
    print_function=print,
    collection_function=run_research_collection_if_due,
):
    print_function()
    print_function("Collecting public research...")
    result = collection_function(database_path)

    if result["status"] == "skipped":
        print_function("Research was already collected today.")

        return result

    print_function(
        "New research items:",
        result["run"]["new_item_count"],
    )
    print_function("Status:", result["status"])

    if result["run"]["error_summary"]:
        print_function(
            "Source note:",
            result["run"]["error_summary"],
        )

    return result


def run_view_public_research_inbox(
    database_path,
    print_function=print,
):
    research_items = get_latest_research_items(
        database_path,
        limit=10,
    )

    print_function()
    print_function("--- Public Research Inbox ---")

    if not research_items:
        print_function("No public research has been collected yet.")

        return research_items

    print_function("Source labels describe the link, not its reliability.")

    for item in research_items:
        source_info = describe_research_source(item["url"])
        print_function()
        print_function("Source:", item["source"])
        print_function("Link domain:", source_info["domain"])
        print_function("Source type (URL-based):", source_info["source_type"])
        print_function("Evidence: Public metadata; claims not verified by SK.")
        print_function("Title:", item["title"])
        print_function("Link:", item["url"])

        if item["published_at"]:
            print_function("Published:", item["published_at"])

        if item["summary"]:
            print_function("Summary:", item["summary"])

    return research_items
