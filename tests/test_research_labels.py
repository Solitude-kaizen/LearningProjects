import pytest

from src.solitude_kaizen.research_labels import describe_research_source


@pytest.mark.parametrize(
    "url,domain,source_type",
    [
        ("https://github.com/example/project", "github.com", "Code hosting"),
        ("https://arxiv.org/abs/2609.00001", "arxiv.org", "Preprint archive"),
        (
            "https://export.arxiv.org/abs/2609.00001",
            "export.arxiv.org",
            "Preprint archive",
        ),
        ("https://www.youtube.com/watch?v=test", "www.youtube.com", "Video platform"),
        ("https://youtu.be/test", "youtu.be", "Video platform"),
        (
            "https://news.ycombinator.com/item?id=123",
            "news.ycombinator.com",
            "Discussion forum",
        ),
        ("https://docs.python.org/3/", "docs.python.org", "Documentation site"),
        ("https://docs.nvidia.com/local-ai/", "docs.nvidia.com", "Documentation site"),
        (
            "https://modelcontextprotocol.io/docs/",
            "modelcontextprotocol.io",
            "Documentation site",
        ),
        (
            "https://blog.modelcontextprotocol.io/posts/example/",
            "blog.modelcontextprotocol.io",
            "Project blog",
        ),
    ],
)
def test_known_source_types_are_local_url_hints(url, domain, source_type):
    assert describe_research_source(url) == {
        "domain": domain,
        "source_type": source_type,
    }


@pytest.mark.parametrize(
    "url,domain",
    [
        ("https://example.com/official-verified-docs", "example.com"),
        ("https://docs.python.org.evil.example/", "docs.python.org.evil.example"),
        ("https://evil.example/?next=https://github.com/", "evil.example"),
        ("https://github.com.evil.example/project", "github.com.evil.example"),
        ("http://127.0.0.1/", "127.0.0.1"),
    ],
)
def test_unknown_or_lookalike_hosts_do_not_gain_recognized_labels(url, domain):
    assert describe_research_source(url) == {
        "domain": domain,
        "source_type": "Unknown",
    }


@pytest.mark.parametrize(
    "url",
    [
        None,
        123,
        "",
        "github.com/example/project",
        "//github.com/example/project",
        "file:///tmp/example",
        "javascript:alert('test')",
        "https://github.com@evil.example/",
        "https://user:password@docs.python.org/3/",
        "https://[broken/",
        "https://docs.python.org:99999/",
        "https://docs.python.org:8443/",
        "https://docs.py\nthon.org/3/",
        "https://docs.python.org/has space",
        "https://docs.python.org\\@evil.example/",
    ],
)
def test_unsupported_or_malformed_urls_get_no_source_hint(url):
    assert describe_research_source(url) == {
        "domain": "Unavailable",
        "source_type": "Unknown",
    }


@pytest.mark.parametrize(
    "url",
    [
        "HTTPS://DOCS.PYTHON.ORG/3/",
        "https://docs.python.org.:443/3/",
        "http://docs.python.org:80/3/",
    ],
)
def test_host_case_standard_ports_and_one_trailing_dot_are_normalized(url):
    assert describe_research_source(url) == {
        "domain": "docs.python.org",
        "source_type": "Documentation site",
    }
