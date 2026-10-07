"""Privacy-friendly web discovery through DuckDuckGo (no API key)."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from ddgs import DDGS
from config import WEB_RESULTS_LIMIT


@dataclass(frozen=True)
class WebSource:
    title: str
    url: str
    snippet: str
    retrieved_at: str


def search_web(query: str, limit: int = WEB_RESULTS_LIMIT) -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).isoformat()
    sources = []
    for item in DDGS().text(query, max_results=max(1, min(limit, 10))):
        url = item.get("href") or item.get("url") or ""
        if url:
            sources.append(asdict(WebSource(item.get("title") or url, url,
                                             item.get("body") or "", now)))
    return sources
