from config import (
    MOCK_MODE,
    AI_FALLBACK_ENABLED,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)

from google import genai
from groq import Groq


# =========================================
# GEMINI CLIENT
# =========================================

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# =========================================
# GROQ CLIENT
# =========================================

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)


# =========================================
# MOCK PLANNER
# =========================================

def mock_plan(task: str):

    return {
        "success": True,
        "agent": "Planner Agent",
        "objective": task,
        "mode": "fallback",

        "plan": f"""
EXECUTION PLAN
==============

OBJECTIVE
{task}

STEP 1 — Define the Objective

Clearly define the business goal and expected outcome.

STEP 2 — Research

Research the target audience, market conditions,
competitors and customer needs.

STEP 3 — Analyze Opportunities

Identify market gaps, customer pain points,
differentiation opportunities and risks.

STEP 4 — Create Strategy

Create a practical strategy based on the
research findings.

STEP 5 — Create Execution Plan

Convert the strategy into actionable tasks.

STEP 6 — Verify

Review the final strategy for completeness,
practicality and consistency.
""",
    }


# =========================================
# GEMINI PLANNER
# =========================================

def gemini_plan(task: str):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are the Planner Agent of FlowPilot AI.

User objective:

{task}

Break the objective into clear executable tasks.

For each task provide:

- Task name
- Description
- Recommended agent
- Required tools
- Expected output

Available agents:

1. Research Agent
2. Marketing Agent
3. Data Agent
4. Content Agent
5. Verification Agent

Create a logical workflow from beginning to end.

Keep the response structured, practical and concise.
"""

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return {
        "success": True,
        "agent": "Planner Agent",
        "objective": task,
        "mode": "gemini",
        "plan": response.text,
    }


# =========================================
# GROQ PLANNER BACKUP
# =========================================

def groq_plan(task: str):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    prompt = f"""
You are the Planner Agent of FlowPilot AI.

User objective:

{task}

Break the objective into clear executable tasks.

For each task provide:

- Task name
- Description
- Recommended agent
- Required tools
- Expected output

Available agents:

1. Research Agent
2. Marketing Agent
3. Data Agent
4. Content Agent
5. Verification Agent

Create a logical workflow from beginning to end.

Keep the response structured, practical and concise.
Do not invent agents.
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional workflow "
                    "planning agent inside FlowPilot AI."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return {
        "success": True,
        "agent": "Planner Agent",
        "objective": task,
        "mode": "groq_backup",
        "plan": content,
    }


# =========================================
# PLANNER AGENT
# =========================================

def planner_agent(task: str):

    # -----------------------------------------
    # MOCK MODE
    # -----------------------------------------

    if MOCK_MODE:
        return mock_plan(task)


    # -----------------------------------------
    # PRIMARY: GEMINI
    # -----------------------------------------

    if gemini_client is not None:

        try:

            print(
                "Planner Agent: trying Gemini..."
            )

            result = gemini_plan(task)

            print(
                "Planner Agent: Gemini succeeded."
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini Planner Error:",
                gemini_error,
            )

    else:

        print(
            "Planner Agent: Gemini is not configured."
        )


    # -----------------------------------------
    # BACKUP: GROQ
    # -----------------------------------------

    if groq_client is not None:

        try:

            print(
                "Planner Agent: trying Groq backup..."
            )

            result = groq_plan(task)

            print(
                "Planner Agent: Groq succeeded."
            )

            return result

        except Exception as groq_error:

            print(
                "Groq Planner Error:",
                groq_error,
            )

    else:

        print(
            "Planner Agent: Groq is not configured."
        )


    # -----------------------------------------
    # FINAL FALLBACK
    # -----------------------------------------

    if AI_FALLBACK_ENABLED:

        print(
            "Planner Agent: using development fallback..."
        )

        return mock_plan(task)


    # -----------------------------------------
    # COMPLETE FAILURE
    # -----------------------------------------

    return {
        "success": False,
        "agent": "Planner Agent",
        "objective": task,
        "error": (
            "All available planning providers "
            "failed."
        ),
    }