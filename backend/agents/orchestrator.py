import json

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

from tools.web_search import web_search


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
# AVAILABLE TOOLS
# =========================================

AVAILABLE_TOOLS = [
    "web_search",
]


# =========================================
# TOOL DETECTION
# =========================================

def detect_tools(task: str):
    """
    Decide whether the user's task requires
    an external tool.
    """

    task_lower = task.lower()

    search_keywords = [
        "research",
        "current",
        "latest",
        "market",
        "competitor",
        "competition",
        "trend",
        "trends",
        "industry",
        "news",
        "search",
        "web",
    ]

    requires_search = any(
        keyword in task_lower
        for keyword in search_keywords
    )

    if requires_search:
        return {
            "requires_tools": True,
            "tools": [
                "web_search",
            ],
        }

    return {
        "requires_tools": False,
        "tools": [],
    }


# =========================================
# EXECUTE TOOLS
# =========================================

def execute_tools(task: str, tool_plan: dict):
    """
    Execute the tools selected by the orchestrator.
    """

    results = []

    if not tool_plan.get("requires_tools"):
        return results

    if "web_search" in tool_plan.get("tools", []):

        print(
            "Orchestrator Agent: executing web_search tool..."
        )

        search_result = web_search(task)

        results.append(search_result)

        print(
            "Orchestrator Agent: web_search completed."
        )

    return results


# =========================================
# MOCK ORCHESTRATOR
# =========================================

def mock_orchestration(task: str):

    tool_plan = detect_tools(task)

    return {
        "success": True,
        "agent": "Orchestrator Agent",
        "objective": task,
        "mode": "fallback",

        "orchestration": {
            "selected_agents": [
                "Planner Agent",
                "Research Agent",
                "Marketing Agent",
                "Verification Agent",
            ],

            "execution_order": [
                "Planner Agent",
                "Research Agent",
                "Marketing Agent",
                "Verification Agent",
            ],

            "reasoning": (
                "The workflow uses planning, research, "
                "marketing strategy generation and final "
                "verification."
            ),
        },

        "tools": tool_plan,
    }


# =========================================
# GEMINI ORCHESTRATOR
# =========================================

def gemini_orchestration(task: str):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are the Orchestrator Agent of FlowPilot AI.

User objective:
{task}

Available agents:

1. Planner Agent
2. Research Agent
3. Marketing Agent
4. Verification Agent

Available tools:

1. web_search

Your responsibilities:

- Understand the user's objective.
- Select only necessary agents.
- Always include Verification Agent.
- Decide the correct execution order.
- Decide whether a tool is required.
- Use web_search when current or external information
  would improve the workflow.
- Do not invent agents.
- Do not invent tools.

Return ONLY valid JSON:

{{
    "selected_agents": [],
    "execution_order": [],
    "reasoning": "",
    "tools": {{
        "requires_tools": false,
        "tools": []
    }}
}}
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
        "agent": "Orchestrator Agent",
        "objective": task,
        "mode": "gemini",
        "orchestration": response.text,
    }


# =========================================
# GROQ ORCHESTRATOR BACKUP
# =========================================

def groq_orchestration(task: str):

    if groq_client is None:
        raise RuntimeError(
            "Groq API key is not configured."
        )

    prompt = f"""
You are the Orchestrator Agent of FlowPilot AI.

User objective:
{task}

Available agents:

1. Planner Agent
2. Research Agent
3. Marketing Agent
4. Verification Agent

Available tools:

1. web_search

Your responsibilities:

- Understand the user's objective.
- Select only necessary agents.
- Always include Verification Agent.
- Decide the correct execution order.
- Decide whether a tool is required.
- Use web_search when current or external information
  would improve the workflow.
- Do not invent agents.
- Do not invent tools.

Return ONLY valid JSON:

{{
    "selected_agents": [],
    "execution_order": [],
    "reasoning": "",
    "tools": {{
        "requires_tools": false,
        "tools": []
    }}
}}
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional workflow "
                    "orchestration agent inside FlowPilot AI."
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
        "agent": "Orchestrator Agent",
        "objective": task,
        "mode": "groq_backup",
        "orchestration": content,
    }


# =========================================
# EXTRACT TOOL PLAN
# =========================================

def get_tool_plan(result: dict, task: str):

    orchestration = result.get(
        "orchestration"
    )

    if isinstance(orchestration, dict):

        tools = orchestration.get("tools")

        if isinstance(tools, dict):
            return tools

    if isinstance(orchestration, str):

        try:

            cleaned = orchestration.strip()

            if cleaned.startswith("```"):
                cleaned = (
                    cleaned
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            parsed = json.loads(cleaned)

            tools = parsed.get("tools")

            if isinstance(tools, dict):
                return tools

        except Exception:
            pass

    # Safe fallback if the AI response could not
    # be parsed as JSON.
    return detect_tools(task)


# =========================================
# ORCHESTRATOR AGENT
# =========================================

def orchestrator_agent(task: str):

    # -----------------------------------------
    # MOCK MODE
    # -----------------------------------------

    if MOCK_MODE:

        result = mock_orchestration(task)

        tool_plan = result.get(
            "tools",
            detect_tools(task),
        )

        result["tool_results"] = execute_tools(
            task,
            tool_plan,
        )

        return result


    # -----------------------------------------
    # PRIMARY: GEMINI
    # -----------------------------------------

    if gemini_client is not None:

        try:

            print(
                "Orchestrator Agent: trying Gemini..."
            )

            result = gemini_orchestration(task)

            print(
                "Orchestrator Agent: Gemini succeeded."
            )

            tool_plan = get_tool_plan(
                result,
                task,
            )

            result["tools"] = tool_plan

            result["tool_results"] = execute_tools(
                task,
                tool_plan,
            )

            return result

        except Exception as gemini_error:

            print(
                "Gemini Orchestrator Error:",
                gemini_error,
            )

    else:

        print(
            "Orchestrator Agent: Gemini is not configured."
        )


    # -----------------------------------------
    # BACKUP: GROQ
    # -----------------------------------------

    if groq_client is not None:

        try:

            print(
                "Orchestrator Agent: trying Groq backup..."
            )

            result = groq_orchestration(task)

            print(
                "Orchestrator Agent: Groq succeeded."
            )

            tool_plan = get_tool_plan(
                result,
                task,
            )

            result["tools"] = tool_plan

            result["tool_results"] = execute_tools(
                task,
                tool_plan,
            )

            return result

        except Exception as groq_error:

            print(
                "Groq Orchestrator Error:",
                groq_error,
            )

    else:

        print(
            "Orchestrator Agent: Groq is not configured."
        )


    # -----------------------------------------
    # FINAL FALLBACK
    # -----------------------------------------

    if AI_FALLBACK_ENABLED:

        print(
            "Orchestrator Agent: "
            "using development fallback..."
        )

        result = mock_orchestration(task)

        tool_plan = result.get(
            "tools",
            detect_tools(task),
        )

        result["tool_results"] = execute_tools(
            task,
            tool_plan,
        )

        return result


    # -----------------------------------------
    # COMPLETE FAILURE
    # -----------------------------------------

    return {
        "success": False,
        "agent": "Orchestrator Agent",
        "objective": task,
        "error": (
            "All available orchestration providers "
            "failed."
        ),
    }