import re
import html
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


def clean_title(title: str) -> str:
    """Clean up a search-result or webpage title."""
    if not title:
        return ""

    title = html.unescape(title)
    title = re.sub(r"\s+", " ", title).strip()

    # Remove search-engine labels such as [PDF] and [HTML].
    title = re.sub(
        r"^(?:\[(?:PDF|HTML|PREPRINT)\]\s*)+",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return title.strip()


def is_suspicious_title(title: str) -> bool:
    """Detect titles that may contain multiple concatenated results."""
    return (
        len(title) > 120
        or title.count("...") >= 2
        or title.count("[PDF]") > 1
    )


def get_canonical_title(url: str) -> str:
    """
    Try to obtain the actual title from the source webpage.
    Return an empty string if it cannot be retrieved reliably.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()

    lookup_url = url

    # An arXiv abstract page is more suitable for title extraction
    # than its PDF download URL.
    if "arxiv.org" in parsed.netloc.lower() and "/pdf/" in path:
        paper_id = path.split("/pdf/", 1)[1].replace(".pdf", "")
        lookup_url = f"https://arxiv.org/abs/{paper_id}"

    else:
        # Avoid treating the contents of a PDF download as HTML.
        if path.endswith(".pdf") or "/content/pdf/" in path:
            return ""

    try:
        response = requests.get(
            lookup_url,
            timeout=7,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "html" not in content_type:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        candidates = []

        # Prefer explicit article metadata.
        for attrs in (
            {"property": "og:title"},
            {"name": "twitter:title"},
        ):
            tag = soup.find("meta", attrs=attrs)

            if tag and tag.get("content"):
                candidates.append(tag["content"])

        # Fall back to the document title and main heading.
        if soup.title:
            candidates.append(soup.title.get_text(" ", strip=True))

        heading = soup.find("h1")

        if heading:
            candidates.append(heading.get_text(" ", strip=True))

        for candidate in candidates:
            candidate = clean_title(candidate)

            if len(candidate) < 8:
                continue

            if candidate.lower() in {
                "forbidden",
                "access denied",
                "just a moment...",
            }:
                continue

            return candidate

    except requests.RequestException as exc:
        print(f"Could not retrieve page title for {url}: {exc}")

    return ""


def fallback_title(title: str) -> str:
    """
    If metadata is unavailable, avoid displaying a huge concatenation
    of several search-result titles.
    """
    title = clean_title(title)

    if len(title) > 180:
        # Search engines often separate truncated titles with ellipses.
        first_part = re.split(r"\s*(?:\.{3,}|…)\s*", title, maxsplit=1)[0]

        if len(first_part) >= 20:
            return first_part.strip()

        # Last resort: limit the displayed title.
        shortened = title[:157].rsplit(" ", 1)[0]
        return shortened.rstrip(" .") + "…"

    return title


def repair_title(result: dict) -> dict:
    """Improve a suspicious search-result title without losing its URL."""
    title = clean_title(result.get("title", ""))
    url = result.get("url", "")

    if is_suspicious_title(title):
        canonical_title = get_canonical_title(url)

        if canonical_title:
            title = canonical_title
        else:
            title = fallback_title(title)

    result["title"] = title or "Untitled source"

    return result


def search_web(query: str, max_results: int = 3):
    search_queries = [
        f"{query} research paper arxiv",
        f"{query} research paper PDF",
        f"{query} machine learning study",
    ]

    all_results = []

    for search_query in search_queries:
        try:
            results = DDGS().text(
                search_query,
                max_results=max_results,
            )

            for result in results:
                title = result.get("title")
                url = result.get("href")
                snippet = result.get("body")

                if not title or not url:
                    continue

                all_results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet or "",
                })

        except Exception as exc:
            print(f"Search failed for '{search_query}': {exc}")

    # Remove duplicate URLs.
    unique_results = []
    seen_urls = set()

    for result in all_results:
        url = result["url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_results.append(result)

    # Prefer research-friendly sources.
    def source_score(result):
        url = result["url"].lower()

        score = 0

        if "arxiv.org" in url:
            score += 5

        if url.endswith(".pdf"):
            score += 4

        if "springer.com" in url:
            score += 3

        if "mdpi.com" in url:
            score += 3

        if "sciencedirect.com" in url:
            score += 1

        if "researchgate.net" in url:
            score -= 2

        return score

    unique_results.sort(
        key=source_score,
        reverse=True,
    )

    # Repair titles only for the results we will return.
    selected_results = unique_results[:max_results]

    for result in selected_results:
        repair_title(result)

    return selected_results


if __name__ == "__main__":
    results = search_web(
        "machine learning models house price prediction",
        max_results=5,
    )

    print("\nResearch Sources Found:\n")

    for index, result in enumerate(results, 1):
        print(f"\n--- Source {index} ---")
        print("Title:", result["title"])
        print("URL:", result["url"])
        print("Snippet:", result["snippet"])