---
name: ddg-search
description: DuckDuckGo web search. No API key required, no rate limits. Reliable fallback when Jina/Brave APIs are unavailable.
---

# DuckDuckGo Search

Web search via DuckDuckGo HTML interface. No API key needed, works out of the box.

## Usage

```bash
{baseDir}/search.py "your search query"
```

## Examples

```bash
# Basic search
{baseDir}/search.py "CozoDB graph algorithms"

# Search for docs
{baseDir}/search.py "Datomic transaction functions documentation"

# Recent topics
{baseDir}/search.py "XTDB v2 XTQL 2025"
```

## Output Format

Returns markdown-formatted search results:

```
## Search Results for: query

[Title](https://example.com)
Description snippet...

[Title 2](https://example.com/page2)
Another snippet...
```

## When to Use

- **Primary search tool** when no Jina/Brave API keys are configured
- Reliable fallback that never rate-limits
- Any web search task
