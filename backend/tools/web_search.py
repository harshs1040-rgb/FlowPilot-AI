# =========================================
# FLOWPILOT AI — REAL WEB SEARCH TOOL
# =========================================

import time

from ddgs import DDGS


def web_search(query: str, max_results: int = 5):
    """
    Search the web using DuckDuckGo.
    Retries automatically if the first request fails.
    """

    last_error = None

    for attempt in range(3):

        try:
            results = []

            with DDGS(timeout=15) as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=max_results,
                )

                for item in search_results:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", ""),
                        }
                    )

            return {
                "success": True,
                "tool": "web_search",
                "query": query,
                "results": results,
            }

        except Exception as error:

            last_error = str(error)

            print(
                f"Web search attempt {attempt + 1}/3 failed: "
                f"{last_error}"
            )

            if attempt < 2:
                time.sleep(2)

    return {
        "success": False,
        "tool": "web_search",
        "query": query,
        "results": [],
        "error": last_error,
    }