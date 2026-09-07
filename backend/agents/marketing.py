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
# FALLBACK MARKETING
# =========================================

def mock_marketing(
    task: str,
    planner_output: str,
    research_output: str,
):

    return {
        "success": True,
        "agent": "Marketing Agent",
        "objective": task,
        "mode": "fallback",
        "based_on_planner": True,
        "based_on_research": True,

        "marketing_plan": f"""
MARKETING STRATEGY
==================

BUSINESS OBJECTIVE
{task}

1. TARGET AUDIENCE

Identify the people most likely to need
this product or service.

Consider:

- Age group
- Student/professional profile
- Location
- Interests
- Purchasing ability
- Main problems

2. CUSTOMER PAIN POINTS

Identify the major problems faced by
the target audience.

Focus on:

- Cost
- Convenience
- Accessibility
- Time
- Existing alternatives
- User experience

3. VALUE PROPOSITION

Clearly explain why customers should
choose this solution instead of alternatives.

4. MARKETING CHANNELS

Potential channels:

- Website
- Search engines
- Social media
- Email
- Online communities
- Referral programs
- Partnerships

5. CONTENT STRATEGY

Create content around:

- Customer problems
- Educational information
- Product benefits
- Demonstrations
- FAQs
- Success stories

6. CUSTOMER ACQUISITION

Possible strategies:

- Free introductory offer
- Referral program
- Social media campaigns
- Search-based content
- Partnerships
- Community marketing

7. 30-DAY ACTION PLAN

WEEK 1
Define target audience, positioning
and messaging.

WEEK 2
Create landing page and initial content.

WEEK 3
Launch campaigns and collect feedback.

WEEK 4
Analyze performance and improve
high-performing channels.

8. KPIs

Track:

- Website visitors
- Leads
- Conversion rate
- Customer acquisition cost
- Engagement
- Retention
- Referral rate

DEVELOPMENT NOTE

This is a development fallback strategy.
Live research data was unavailable.
""",
    }


# =========================================
# GEMINI MARKETING
# =========================================

def gemini_marketing(
    task: str,
    planner_output: str,
    research_output: str,
):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are the Marketing Agent of FlowPilot AI.

Original user objective:

{task}

Planner Agent workflow:

{planner_output}

Research Agent findings:

{research_output}

Create a practical marketing strategy
specifically for this business objective.

Include:

1. Target audience
2. Customer pain points
3. Value proposition
4. Marketing channels
5. Content strategy
6. Social media strategy
7. Customer acquisition strategy
8. 30-day action plan
9. KPIs

Requirements:

- Be specific to the user's objective.
- Do not use unrelated industries.
- Use planner information.
- Use research information.
- Do not invent statistics.
- Clearly identify assumptions.
- Keep the strategy actionable.

Return only the completed marketing strategy.
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
        "agent": "Marketing Agent",
        "objective": task,
        "mode": "gemini",
        "based_on_planner": True,
        "based_on_research": True,
        "marketing_plan": response.text,
    }


# =========================================
# GROQ MARKETING BACKUP
# =========================================

def groq_marketing(
    task: str,
    planner_output: str,
    research_output: str,
):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    prompt = f"""
You are the Marketing Agent of FlowPilot AI.

Original user objective:

{task}

Planner Agent workflow:

{planner_output}

Research Agent findings:

{research_output}

Create a practical marketing strategy
specifically for this business objective.

Include:

1. Target audience
2. Customer pain points
3. Value proposition
4. Marketing channels
5. Content strategy
6. Social media strategy
7. Customer acquisition strategy
8. 30-day action plan
9. KPIs

Requirements:

- Be specific to the user's objective.
- Use the planner information.
- Use the research information.
- Do not invent statistics.
- Clearly identify assumptions.
- Keep the strategy actionable.
- Do not pretend that information is live
  or web-verified.
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional marketing "
                    "strategist working inside FlowPilot AI."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return {
        "success": True,
        "agent": "Marketing Agent",
        "objective": task,
        "mode": "groq_backup",
        "based_on_planner": True,
        "based_on_research": True,
        "marketing_plan": content,
    }


# =========================================
# MARKETING AGENT
# =========================================

def marketing_agent(
    task: str,
    planner_output: str,
    research_output: str,
):

    # -----------------------------------------
    # MOCK MODE
    # -----------------------------------------

    if MOCK_MODE:

        return mock_marketing(
            task,
            planner_output,
            research_output,
        )


    # -----------------------------------------
    # PRIMARY: GEMINI
    # -----------------------------------------

    if gemini_client is not None:

        try:

            print(
                "Marketing Agent: trying Gemini..."
            )

            result = gemini_marketing(
                task,
                planner_output,
                research_output,
            )

            print(
                "Marketing Agent: Gemini succeeded."
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini Marketing Error:",
                gemini_error,
            )

    else:

        print(
            "Marketing Agent: Gemini is not configured."
        )


    # -----------------------------------------
    # BACKUP: GROQ
    # -----------------------------------------

    if groq_client is not None:

        try:

            print(
                "Marketing Agent: trying Groq backup..."
            )

            result = groq_marketing(
                task,
                planner_output,
                research_output,
            )

            print(
                "Marketing Agent: Groq succeeded."
            )

            return result

        except Exception as groq_error:

            print(
                "Groq Marketing Error:",
                groq_error,
            )

    else:

        print(
            "Marketing Agent: Groq is not configured."
        )


    # -----------------------------------------
    # FINAL FALLBACK
    # -----------------------------------------

    if AI_FALLBACK_ENABLED:

        print(
            "Marketing Agent: using development fallback..."
        )

        return mock_marketing(
            task,
            planner_output,
            research_output,
        )


    # -----------------------------------------
    # COMPLETE FAILURE
    # -----------------------------------------

    return {
        "success": False,
        "agent": "Marketing Agent",
        "objective": task,
        "error": (
            "All available marketing providers "
            "failed."
        ),
    }