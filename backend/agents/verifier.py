import re

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
# PARSE VERIFICATION RESULT
# =========================================

def parse_verification(text: str):
    """
    Extract structured verification information
    from the AI-generated verification report.
    """

    status_match = re.search(
        r"VERIFICATION STATUS:\s*(PASS|NEEDS_IMPROVEMENT)",
        text,
        re.IGNORECASE,
    )

    score_match = re.search(
        r"QUALITY SCORE:\s*(10|[1-9])\s*/\s*10",
        text,
        re.IGNORECASE,
    )

    status = (
        status_match.group(1).upper()
        if status_match
        else "NEEDS_IMPROVEMENT"
    )

    quality_score = (
        int(score_match.group(1))
        if score_match
        else None
    )

    return {
        "status": status,
        "quality_score": quality_score,
    }


# =========================================
# FALLBACK VERIFICATION
# =========================================

def mock_verification(
    task: str,
    generated_plan: str,
):

    verification_text = """
VERIFICATION STATUS:
PASS

QUALITY SCORE:
8/10

STRENGTHS:

- The workflow addresses the business objective.
- Planning is included.
- Research is included.
- Marketing strategy is included.
- The final workflow includes measurable KPIs.
- The workflow has a verification stage.

ISSUES:

- The current result uses development fallback data.
- Live market research requires external research data.
- More business-specific information would improve accuracy.

IMPROVEMENTS:

- Connect live research tools.
- Add competitor data.
- Add user-specific business information.
- Add human approval for sensitive actions.

FINAL VERDICT:

The workflow is structurally complete and suitable
for development testing.
"""

    parsed = parse_verification(verification_text)

    return {
        "success": True,
        "agent": "Verification Agent",
        "objective": task,
        "mode": "fallback",

        "verification": verification_text,

        "status": parsed["status"],
        "quality_score": parsed["quality_score"],
    }


# =========================================
# GEMINI VERIFICATION
# =========================================

def gemini_verification(
    task: str,
    generated_plan: str,
):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are the Verification Agent of FlowPilot AI.

Original user objective:

{task}

Generated strategy:

{generated_plan}

Evaluate the strategy carefully.

Check:

1. Does it address the user's objective?
2. Is the strategy complete?
3. Are recommendations practical?
4. Are steps logically organized?
5. Are there unsupported claims?
6. What important information is missing?
7. How can the strategy improve?

Return EXACTLY this structure:

VERIFICATION STATUS:
PASS or NEEDS_IMPROVEMENT

QUALITY SCORE:
1-10/10

STRENGTHS:
Major strengths.

ISSUES:
Weaknesses or missing information.

IMPROVEMENTS:
Specific improvements.

FINAL VERDICT:
Whether the strategy is ready to use.

Rules:

- Base the verification only on the provided strategy.
- Do not invent facts.
- Identify unsupported claims.
- Be objective and critical.
- Give practical improvements.
"""

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    verification_text = response.text

    parsed = parse_verification(
        verification_text
    )

    return {
        "success": True,
        "agent": "Verification Agent",
        "objective": task,
        "mode": "gemini",

        "verification": verification_text,

        "status": parsed["status"],
        "quality_score": parsed["quality_score"],
    }


# =========================================
# GROQ VERIFICATION BACKUP
# =========================================

def groq_verification(
    task: str,
    generated_plan: str,
):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    prompt = f"""
You are the Verification Agent of FlowPilot AI.

Original user objective:

{task}

Generated strategy:

{generated_plan}

Evaluate the strategy carefully.

Check:

1. Does it address the user's objective?
2. Is the strategy complete?
3. Are recommendations practical?
4. Are steps logically organized?
5. Are there unsupported claims?
6. What important information is missing?
7. How can the strategy improve?

Return EXACTLY this structure:

VERIFICATION STATUS:
PASS or NEEDS_IMPROVEMENT

QUALITY SCORE:
1-10/10

STRENGTHS:
Major strengths.

ISSUES:
Weaknesses or missing information.

IMPROVEMENTS:
Specific improvements.

FINAL VERDICT:
Whether the strategy is ready to use.

Rules:

- Base the verification only on the provided strategy.
- Do not invent facts.
- Clearly identify unsupported claims.
- Be objective and critical.
- Give practical improvements.
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional quality "
                    "assurance and verification analyst "
                    "working inside FlowPilot AI."
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

    parsed = parse_verification(content)

    return {
        "success": True,
        "agent": "Verification Agent",
        "objective": task,
        "mode": "groq_backup",

        "verification": content,

        "status": parsed["status"],
        "quality_score": parsed["quality_score"],
    }


# =========================================
# VERIFICATION AGENT
# =========================================

def verifier_agent(
    task: str,
    generated_plan: str,
):

    # -----------------------------------------
    # MOCK MODE
    # -----------------------------------------

    if MOCK_MODE:

        return mock_verification(
            task,
            generated_plan,
        )


    # -----------------------------------------
    # PRIMARY: GEMINI
    # -----------------------------------------

    if gemini_client is not None:

        try:

            print(
                "Verification Agent: trying Gemini..."
            )

            result = gemini_verification(
                task,
                generated_plan,
            )

            print(
                "Verification Agent: Gemini succeeded."
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini Verification Error:",
                gemini_error,
            )

    else:

        print(
            "Verification Agent: Gemini is not configured."
        )


    # -----------------------------------------
    # BACKUP: GROQ
    # -----------------------------------------

    if groq_client is not None:

        try:

            print(
                "Verification Agent: trying Groq backup..."
            )

            result = groq_verification(
                task,
                generated_plan,
            )

            print(
                "Verification Agent: Groq succeeded."
            )

            return result

        except Exception as groq_error:

            print(
                "Groq Verification Error:",
                groq_error,
            )

    else:

        print(
            "Verification Agent: Groq is not configured."
        )


    # -----------------------------------------
    # FINAL FALLBACK
    # -----------------------------------------

    if AI_FALLBACK_ENABLED:

        print(
            "Verification Agent: using development fallback..."
        )

        return mock_verification(
            task,
            generated_plan,
        )


    # -----------------------------------------
    # COMPLETE FAILURE
    # -----------------------------------------

    return {
        "success": False,
        "agent": "Verification Agent",
        "objective": task,
        "status": "FAILED",
        "quality_score": None,
        "error": (
            "All available verification providers "
            "failed."
        ),
    }