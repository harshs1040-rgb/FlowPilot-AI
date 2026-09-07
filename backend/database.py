import json

from sqlmodel import SQLModel, Session, create_engine

from config import DB_URL
from models import WorkflowHistory, User


# =========================================
# DATABASE ENGINE
# =========================================

engine = create_engine(
    DB_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    ),
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


# =========================================
# USER DATABASE FUNCTIONS
# =========================================

def get_user_by_email(email: str):
    from sqlmodel import select

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()


def create_user(
    email: str,
    password_hash: str,
):
    with Session(engine) as session:

        user = User(
            email=email,
            password_hash=password_hash,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user