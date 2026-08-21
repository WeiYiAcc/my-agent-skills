#!/usr/bin/env python3
"""DuckDuckGo HTML search — no API key required, reliable fallback."""

import sys
import re
import urllib.request
import urllib.parse

TIMEOUT = 15
MAX_RESULTS = 8


def search(query, num_results=MAX_RESULTS):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract result links — href may appear before or after class
    results = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html
    )
    if not results:
        results = re.findall(
            r'<a[^>]*href="([^"]+)"[^>]*class="result__a"[^>]*>(.*?)</a>', html
        )

    # Extract snippets
    snippets = re.findall(
        r'class="result__snippet"[^>]*>(.*?)</(?:a|span|td|div)>',
        html,
        re.DOTALL,
    )

    print(f"## Search Results for: {query}\n")

    count = 0
    for i, (href, title) in enumerate(results):
        if count >= num_results:
            break

        # Clean HTML tags
        title = re.sub(r"<[^>]+>", "", title).strip()
        if not title:
            continue

        # Decode DDG redirect URL
        if "uddg=" in href:
            try:
                raw = href.split("uddg=")[1].split("&amp;")[0].split("&")[0]
                href = urllib.parse.unquote(raw)
            except Exception:
                pass
        # Strip leading // protocol-relative
        if href.startswith("//"):
            href = "https:" + href

        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()

        print(f"[{title}]({href})")
        if snippet:
            print(f"{snippet[:300]}")
        print()
        count += 1

    if count == 0:
        print("No results found.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: search.py <query>", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    search(query)
