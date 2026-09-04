from urllib.parse import urlsplit


# Exact-host hints only: neither a quality score nor permission to access a URL.
SOURCE_TYPES_BY_HOST = {
    "github.com": "Code hosting",
    "www.github.com": "Code hosting",
    "arxiv.org": "Preprint archive",
    "www.arxiv.org": "Preprint archive",
    "export.arxiv.org": "Preprint archive",
    "youtube.com": "Video platform",
    "www.youtube.com": "Video platform",
    "youtu.be": "Video platform",
    "news.ycombinator.com": "Discussion forum",
    "docs.python.org": "Documentation site",
    "docs.nvidia.com": "Documentation site",
    "modelcontextprotocol.io": "Documentation site",
    "blog.modelcontextprotocol.io": "Project blog",
}


def describe_research_source(url):
    """Describe a stored URL locally; do not fetch or verify its contents."""
    unknown = {"domain": "Unavailable", "source_type": "Unknown"}
    if not isinstance(url, str) or not url:
        return unknown

    # Reject characters that URL parsers may silently strip or interpret
    # differently. This is conservative labeling, not a network sandbox.
    if any(
        character.isspace()
        or ord(character) < 32
        or ord(character) == 127
        or character == "\\"
        for character in url
    ):
        return unknown

    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return unknown
        default_port = 443 if parsed.scheme == "https" else 80
        if parsed.port is not None and parsed.port != default_port:
            return unknown
        domain = parsed.hostname.lower().removesuffix(".")
    except ValueError:
        return unknown

    return {
        "domain": domain,
        "source_type": SOURCE_TYPES_BY_HOST.get(domain, "Unknown"),
    }
