import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from database import create_db_and_tables, save_workflow
from models import WorkflowHistory

from agents.orchestrator import orchestrator_agent
from agents.planner import planner_agent
from agents.research import research_agent
from agents.marketing import marketing_agent
from agents.verifier import verifier_agent


# =========================================
# DATABASE STARTUP
# =========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# =========================================
# FASTAPI APPLICATION
# =========================================

app = FastAPI(
    title="FlowPilot AI",
    description="Multi-Agent Business Automation Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://flow-pilot-ai-eight.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# ROOT
# =========================================

@app.get("/")
def root():
    return {
        "name": "FlowPilot AI",
        "status": "running",
        "version": "1.0.0",
    }


# =========================================
# HEALTH CHECK
# =========================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "FlowPilot AI",
    }


# =========================================
# ORCHESTRATE
# =========================================

@app.post("/orchestrate")
def orchestrate(
    task: str = Query(...),
):
    return orchestrator_agent(task)


# =========================================
# PLAN
# =========================================

@app.post("/plan")
def plan(
    task: str = Query(...),
):
    return planner_agent(task)


# =========================================
# RESEARCH
# =========================================

@app.post("/research")
def research(
    task: str = Query(...),
):
    planner_result = planner_agent(task)

    planner_output = planner_result.get(
        "plan",
        "",
    )

    return research_agent(
        task,
        planner_output,
    )


# =========================================
# MARKETING
# =========================================

@app.post("/marketing")
def marketing(
    task: str = Query(...),
):
    planner_result = planner_agent(task)

    planner_output = planner_result.get(
        "plan",
        "",
    )

    research_result = research_agent(
        task,
        planner_output,
    )

    research_output = research_result.get(
        "research",
        "",
    )

    return marketing_agent(
        task,
        planner_output,
        research_output,
    )


# =========================================
# COMPLETE WORKFLOW
# =========================================

@app.post("/run")
def run_workflow(
    task: str = Query(...),
):

    # -------------------------------
    # 1. ORCHESTRATOR
    # -------------------------------

    orchestrator_result = orchestrator_agent(
        task
    )

    # -------------------------------
    # 2. PLANNER
    # -------------------------------

    planner_result = planner_agent(
        task
    )

    planner_output = planner_result.get(
        "plan",
        "",
    )

    # -------------------------------
    # 3. RESEARCH
    # -------------------------------

    research_result = research_agent(
        task,
        planner_output,
    )

    research_output = research_result.get(
        "research",
        "",
    )

    # -------------------------------
    # 4. MARKETING
    # -------------------------------

    marketing_result = marketing_agent(
        task,
        planner_output,
        research_output,
    )

    marketing_output = marketing_result.get(
        "marketing_plan",
        "",
    )

    # -------------------------------
    # 5. VERIFICATION
    # -------------------------------

    verification_result = verifier_agent(
        task,
        marketing_output,
    )

    # -------------------------------
    # FINAL RESULT
    # -------------------------------

    final_result = {
        "success": True,
        "objective": task,
        "orchestrator": orchestrator_result,
        "planner": planner_result,
        "research": research_result,
        "marketing": marketing_result,
        "verification": verification_result,
    }

    # -------------------------------
    # SAVE TO DATABASE
    # -------------------------------

    save_workflow(
        task,
        final_result,
        "completed",
    )

    return final_result


# =========================================
# WORKFLOW HISTORY
# =========================================

@app.get("/history")
def get_history():

    from sqlmodel import Session, select

    with Session(
        __import__("database").engine
    ) as session:

        workflows = session.exec(
            select(WorkflowHistory)
            .order_by(
                WorkflowHistory.created_at.desc()
            )
        ).all()

        return [
            {
                "id": workflow.id,
                "objective": workflow.objective,
                "status": workflow.status,
                "result": json.loads(
                    workflow.result_json
                ),
                "created_at": workflow.created_at.isoformat(),
            }
            for workflow in workflows
        ]


# =========================================
# STREAMING WORKFLOW
# =========================================

@app.get("/run-stream")
async def run_stream(
    task: str = Query(...),
):

    async def event_generator():

        try:

            # =================================
            # ORCHESTRATOR
            # =================================

            yield (
                "event: agent_start\n"
                f"data: {json.dumps({'agent': 'Orchestrator Agent'})}\n\n"
            )

            orchestrator_result = await asyncio.to_thread(
                orchestrator_agent,
                task,
            )

            yield (
                "event: agent_complete\n"
                f"data: {json.dumps({'agent': 'Orchestrator Agent', 'result': orchestrator_result})}\n\n"
            )

            # =================================
            # PLANNER
            # =================================

            yield (
                "event: agent_start\n"
                f"data: {json.dumps({'agent': 'Planner Agent'})}\n\n"
            )

            planner_result = await asyncio.to_thread(
                planner_agent,
                task,
            )

            planner_output = planner_result.get(
                "plan",
                "",
            )

            yield (
                "event: agent_complete\n"
                f"data: {json.dumps({'agent': 'Planner Agent', 'result': planner_result})}\n\n"
            )

            # =================================
            # RESEARCH
            # =================================

            yield (
                "event: agent_start\n"
                f"data: {json.dumps({'agent': 'Research Agent'})}\n\n"
            )

            research_result = await asyncio.to_thread(
                research_agent,
                task,
                planner_output,
            )

            research_output = research_result.get(
                "research",
                "",
            )

            yield (
                "event: agent_complete\n"
                f"data: {json.dumps({'agent': 'Research Agent', 'result': research_result})}\n\n"
            )

            # =================================
            # MARKETING
            # =================================

            yield (
                "event: agent_start\n"
                f"data: {json.dumps({'agent': 'Marketing Agent'})}\n\n"
            )

            marketing_result = await asyncio.to_thread(
                marketing_agent,
                task,
                planner_output,
                research_output,
            )

            marketing_output = marketing_result.get(
                "marketing_plan",
                "",
            )

            yield (
                "event: agent_complete\n"
                f"data: {json.dumps({'agent': 'Marketing Agent', 'result': marketing_result})}\n\n"
            )

            # =================================
            # VERIFICATION
            # =================================

            yield (
                "event: agent_start\n"
                f"data: {json.dumps({'agent': 'Verification Agent'})}\n\n"
            )

            verification_result = await asyncio.to_thread(
                verifier_agent,
                task,
                marketing_output,
            )

            yield (
                "event: agent_complete\n"
                f"data: {json.dumps({'agent': 'Verification Agent', 'result': verification_result})}\n\n"
            )

            # =================================
            # FINAL RESULT
            # =================================

            final_result = {
                "success": True,
                "objective": task,
                "orchestrator": orchestrator_result,
                "planner": planner_result,
                "research": research_result,
                "marketing": marketing_result,
                "verification": verification_result,
            }

            # =================================
            # SAVE WORKFLOW TO POSTGRESQL
            # =================================

            await asyncio.to_thread(
                save_workflow,
                task,
                final_result,
                "completed",
            )

            # =================================
            # WORKFLOW COMPLETE
            # =================================

            yield (
                "event: workflow_complete\n"
                f"data: {json.dumps(final_result)}\n\n"
            )

        except Exception as e:

            error_data = {
                "success": False,
                "error": str(e),
            }

            # =================================
            # SAVE FAILED WORKFLOW
            # =================================

            try:

                await asyncio.to_thread(
                    save_workflow,
                    task,
                    error_data,
                    "failed",
                )

            except Exception:
                pass

            yield (
                "event: error\n"
                f"data: {json.dumps(error_data)}\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )