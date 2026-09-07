# =========================================
# FLOWPILOT AI — RESEARCH AGENT
# FINAL / EXTENSIBLE VERSION
# =========================================

from typing import Any

from config import (
    MOCK_MODE,
    AI_FALLBACK_ENABLED,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)

from google import genai
from google.genai import types
from groq import Groq

from tools.web_search import web_search


# =========================================
# CLIENT INITIALIZATION
# =========================================

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)


# =========================================
# WEB SEARCH
# =========================================

def perform_web_search(
    task: str,
    max_results: int = 5,
) -> dict:
    """
    Perform real web research for the user's
    objective.

    The actual search implementation lives in:

        backend/tools/web_search.py

    Keeping the search tool separate makes it
    easier to replace DuckDuckGo/DDGS later
    with another provider.
    """

    print(
        "Research Agent: performing web search..."
    )

    try:

        result = web_search(
            task,
            max_results=max_results,
        )

        if result.get("success"):

            print(
                "Research Agent: "
                "web search succeeded."
            )

            return result

        print(
            "Research Agent: "
            "web search failed:",
            result.get("error"),
        )

        return result

    except Exception as error:

        print(
            "Research Agent: "
            "web search exception:",
            error,
        )

        return {
            "success": False,
            "tool": "web_search",
            "query": task,
            "results": [],
            "error": str(error),
        }


# =========================================
# FORMAT WEB SEARCH RESULTS
# =========================================

def format_search_results(
    search_result: dict,
) -> str:
    """
    Convert web search results into structured
    readable context for an LLM.
    """

    results = search_result.get(
        "results",
        [],
    )

    if not results:

        return (
            "No web search results were available."
        )

    formatted = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        title = item.get(
            "title",
            "",
        )

        url = item.get(
            "url",
            "",
        )

        snippet = item.get(
            "snippet",
            "",
        )

        formatted.append(
            f"""
SOURCE {index}
-------------
Title: {title}
URL: {url}
Summary: {snippet}
"""
        )

    return "\n".join(formatted)


# =========================================
# EXTRACT SOURCE INFORMATION
# =========================================

def extract_search_sources(
    search_result: dict,
) -> list[dict]:
    """
    Extract clean source information so the
    frontend can later display citations,
    references, or source cards.
    """

    sources = []

    for item in search_result.get(
        "results",
        [],
    ):

        title = item.get(
            "title",
            "",
        )

        url = item.get(
            "url",
            "",
        )

        if title or url:

            sources.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": item.get(
                        "snippet",
                        "",
                    ),
                }
            )

    return sources


# =========================================
# BUILD COMMON RESEARCH CONTEXT
# =========================================

def build_research_context(
    task: str,
    planner_output: str,
    search_context: str,
) -> str:
    """
    Build a consistent research context shared
    by Gemini and Groq.

    This makes provider switching easier later.
    """

    return f"""
USER OBJECTIVE
==============

{task}


PLANNER AGENT OUTPUT
====================

{planner_output}


WEB SEARCH EVIDENCE
===================

{search_context}
"""


# =========================================
# MOCK / DEVELOPMENT FALLBACK
# =========================================

def mock_research(
    task: str,
    planner_output: str,
    search_context: str = "",
    search_sources: list[dict] | None = None,
) -> dict:
    """
    Development fallback used when AI providers
    are unavailable.

    This keeps the rest of the workflow running
    during development and testing.
    """

    if search_sources is None:
        search_sources = []

    return {
        "success": True,
        "agent": "Research Agent",
        "objective": task,
        "mode": "fallback",
        "based_on_planner": True,

        "research": f"""
RESEARCH REPORT
===============

OBJECTIVE
{task}


TARGET AUDIENCE
---------------

Identify the users most likely to benefit
from the product, service, or business.

Consider:

- Demographics
- Location
- Interests
- Needs
- Purchasing ability
- Current alternatives


CUSTOMER PROBLEMS
-----------------

Identify the main problems or unmet needs
experienced by the target audience.


MARKET ANALYSIS
---------------

Analyze:

- Existing demand
- Customer needs
- Market opportunities
- Current alternatives
- Industry direction
- Important trends


COMPETITOR ANALYSIS
-------------------

Identify relevant competitors and compare:

- Product/service
- Features
- Pricing
- Target audience
- Positioning
- Strengths
- Weaknesses


OPPORTUNITIES
-------------

Identify areas where the proposed solution
could differentiate itself.


RISKS
-----

Consider:

- Competition
- Customer acquisition
- Pricing
- Market changes
- Product adoption
- Execution challenges


RECOMMENDATIONS
---------------

Create practical recommendations based on
the objective and available evidence.


KEY FINDINGS FOR MARKETING
--------------------------

Provide concise findings that can be passed
to the Marketing Agent.


NOTE
----

This is a development fallback result.
The actual AI providers were unavailable.
""",

        "planner_context": planner_output,

        "search_query": task,

        "search_sources": search_sources,

        "web_search_results": search_context,

        "evidence_available": bool(
            search_sources
        ),
    }


# =========================================
# GEMINI RESEARCH
# =========================================

def gemini_research(
    task: str,
    planner_output: str,
    search_context: str,
    search_sources: list[dict],
) -> dict:
    """
    Primary Research Agent implementation
    using Gemini.

    Gemini also has access to Google's search
    grounding capability.
    """

    if gemini_client is None:

        raise RuntimeError(
            "Gemini API key is not configured."
        )

    context = build_research_context(
        task,
        planner_output,
        search_context,
    )

    prompt = f"""
You are the Research Agent inside
FlowPilot AI, a multi-agent business
automation platform.

Your job is to perform useful,
specific, evidence-aware research.

{context}


IMPORTANT RESEARCH RULES
========================

1. Research the user's actual objective.

2. Do not produce a generic research template.

3. Use the supplied web-search results as
   evidence.

4. You may also use Google's search grounding
   when available.

5. Do not invent statistics.

6. Do not invent companies, competitors,
   products, market figures, or trends.

7. If a claim is supported by a source,
   identify the source where practical.

8. Clearly distinguish:
   - sourced information
   - reasonable analysis
   - assumptions

9. If evidence is insufficient, explicitly
   say that evidence is insufficient.

10. Do not present assumptions as facts.

11. Prioritize information useful for a
    business decision.

12. Prepare the final findings so they can
    be consumed by the Marketing Agent.


RESEARCH AREAS
==============

Analyze:

1. Research objective
2. Target audience
3. Customer problems
4. Market analysis
5. Current trends
6. Competitor analysis
7. Market opportunities
8. Risks
9. Recommendations
10. Key findings for Marketing


OUTPUT FORMAT
=============

Return a structured professional research
report containing:

- Executive Summary
- Target Audience
- Customer Problems
- Market Analysis
- Trends
- Competitor Analysis
- Opportunities
- Risks
- Recommendations
- Key Findings for Marketing
- Evidence / Sources
- Data Gaps and Assumptions
"""

    search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    generation_config = (
        types.GenerateContentConfig(
            tools=[search_tool]
        )
    )

    response = (
        gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=generation_config,
        )
    )

    if not response.text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    grounded_sources = []

    search_queries = []

    # =====================================
    # GEMINI GROUNDING METADATA
    # =====================================

    try:

        metadata = (
            response
            .candidates[0]
            .grounding_metadata
        )

        if metadata:

            if metadata.web_search_queries:

                search_queries = list(
                    metadata.web_search_queries
                )

            if metadata.grounding_chunks:

                for chunk in (
                    metadata.grounding_chunks
                ):

                    if chunk.web:

                        title = (
                            chunk.web.title
                            or ""
                        )

                        url = (
                            chunk.web.uri
                            or ""
                        )

                        if title or url:

                            grounded_sources.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": "",
                                    "source_type": (
                                        "gemini_grounding"
                                    ),
                                }
                            )

    except Exception as metadata_error:

        print(
            "Grounding metadata warning:",
            metadata_error,
        )

    # =====================================
    # MERGE SOURCES
    # =====================================

    all_sources = []

    seen_urls = set()

    for source in (
        search_sources + grounded_sources
    ):

        url = source.get(
            "url",
            "",
        )

        if url and url in seen_urls:
            continue

        if url:
            seen_urls.add(url)

        source_copy = dict(source)

        if "source_type" not in source_copy:
            source_copy["source_type"] = (
                "web_search"
            )

        all_sources.append(
            source_copy
        )

    return {
        "success": True,
        "agent": "Research Agent",
        "objective": task,
        "mode": "gemini_google_search",
        "based_on_planner": True,

        "research": response.text,

        "planner_context": planner_output,

        "search_query": task,

        "search_queries": search_queries,

        "search_sources": all_sources,

        "sources": all_sources,

        "web_search_results": search_context,

        "evidence_available": bool(
            all_sources
        ),

        "provider": "gemini",
    }


# =========================================
# GROQ RESEARCH
# =========================================

def groq_research(
    task: str,
    planner_output: str,
    search_context: str,
    search_sources: list[dict],
) -> dict:
    """
    Backup Research Agent implementation
    using Groq.

    Groq receives the real web-search context,
    but does not claim independent live
    verification.
    """

    if groq_client is None:

        raise RuntimeError(
            "Groq API key is not configured."
        )

    context = build_research_context(
        task,
        planner_output,
        search_context,
    )

    prompt = f"""
You are the Research Agent inside
FlowPilot AI.

Perform detailed business research based
on the user's objective.

{context}


IMPORTANT
=========

The web-search results above were collected
by FlowPilot's web-search tool.

Use them as evidence.

You do NOT have to pretend that you personally
verified the live web.

RULES:

- Be specific to the user's objective.
- Do not produce a generic template.
- Do not invent statistics.
- Do not invent competitors.
- Do not invent market data.
- Do not present unsupported claims as facts.
- Identify useful source URLs.
- Distinguish evidence from analysis.
- Clearly mention important data gaps.
- Use practical business reasoning.
- Prepare useful findings for the Marketing Agent.


ANALYZE
=======

1. Research objective
2. Target audience
3. Customer problems
4. Market analysis
5. Current trends
6. Competitor analysis
7. Market opportunities
8. Risks
9. Recommendations
10. Key findings for Marketing


OUTPUT
======

Return:

- Executive Summary
- Target Audience
- Customer Problems
- Market Analysis
- Trends
- Competitor Analysis
- Opportunities
- Risks
- Recommendations
- Key Findings for Marketing
- Evidence / Sources
- Data Gaps and Assumptions
"""

    response = (
        groq_client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional "
                        "business research analyst "
                        "inside a multi-agent "
                        "automation platform."
                    ),
                },

                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=0.3,
        )
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise RuntimeError(
            "Groq returned an empty response."
        )

    return {
        "success": True,
        "agent": "Research Agent",
        "objective": task,
        "mode": "groq_backup",
        "based_on_planner": True,

        "research": content,

        "planner_context": planner_output,

        "search_query": task,

        "search_queries": [],

        "search_sources": search_sources,

        "sources": search_sources,

        "web_search_results": search_context,

        "evidence_available": bool(
            search_sources
        ),

        "provider": "groq",

        "note": (
            "Research generated using the "
            "Groq backup provider with real "
            "web-search results supplied by "
            "the FlowPilot web-search tool."
        ),
    }


# =========================================
# RESEARCH AGENT
# =========================================

def research_agent(
    task: str,
    planner_output: str,
) -> dict:
    """
    Main Research Agent entry point.

    Provider priority:

        Web Search
             ↓
        Gemini
             ↓
        Groq
             ↓
        Development Fallback

    This function is intentionally kept stable
    so the Orchestrator does not need to change
    when the AI provider implementation changes.
    """

    # =====================================
    # WEB SEARCH
    # =====================================

    search_result = perform_web_search(
        task,
        max_results=5,
    )

    search_context = format_search_results(
        search_result
    )

    search_sources = extract_search_sources(
        search_result
    )


    # =====================================
    # MOCK MODE
    # =====================================

    if MOCK_MODE:

        print(
            "Research Agent: "
            "using MOCK mode..."
        )

        return mock_research(
            task,
            planner_output,
            search_context,
            search_sources,
        )


    # =====================================
    # PRIMARY PROVIDER — GEMINI
    # =====================================

    if gemini_client is not None:

        try:

            print(
                "Research Agent: "
                "trying Gemini..."
            )

            result = gemini_research(
                task,
                planner_output,
                search_context,
                search_sources,
            )

            print(
                "Research Agent: "
                "Gemini succeeded."
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini Research Error:",
                gemini_error,
            )

    else:

        print(
            "Research Agent: "
            "Gemini is not configured."
        )


    # =====================================
    # BACKUP PROVIDER — GROQ
    # =====================================

    if groq_client is not None:

        try:

            print(
                "Research Agent: "
                "trying Groq backup..."
            )

            result = groq_research(
                task,
                planner_output,
                search_context,
                search_sources,
            )

            print(
                "Research Agent: "
                "Groq succeeded."
            )

            return result

        except Exception as groq_error:

            print(
                "Groq Research Error:",
                groq_error,
            )

    else:

        print(
            "Research Agent: "
            "Groq is not configured."
        )


    # =====================================
    # DEVELOPMENT FALLBACK
    # =====================================

    if AI_FALLBACK_ENABLED:

        print(
            "Research Agent: "
            "using development fallback..."
        )

        return mock_research(
            task,
            planner_output,
            search_context,
            search_sources,
        )


    # =====================================
    # COMPLETE FAILURE
    # =====================================

    return {
        "success": False,
        "agent": "Research Agent",
        "objective": task,

        "mode": "failed",

        "planner_context": planner_output,

        "search_query": task,

        "search_sources": search_sources,

        "web_search_results": search_context,

        "evidence_available": bool(
            search_sources
        ),

        "error": (
            "All available research "
            "providers failed."
        ),
    }