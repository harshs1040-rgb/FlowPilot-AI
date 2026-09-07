import json

from sqlmodel import SQLModel, Session, create_engine

from config import DB_URL
from models import WorkflowHistory


# =========================================
# DATABASE ENGINE
# =========================================

engine = create_engine(
    DB_URL,
    echo=True,
)


# =========================================
# CREATE TABLES
# =========================================

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# =========================================
# SAVE WORKFLOW HISTORY
# =========================================

def save_workflow(
    objective: str,
    result: dict,
    status: str = "completed",
):
    with Session(engine) as session:

        workflow = WorkflowHistory(
            objective=objective,
            status=status,
            result_json=json.dumps(result),
        )

        session.add(workflow)
        session.commit()
        session.refresh(workflow)

        return workflow