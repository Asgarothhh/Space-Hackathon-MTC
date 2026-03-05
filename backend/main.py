from fastapi import FastAPI
import backend.models.auth  # noqa: F401
import backend.models.projects  # noqa: F401
import backend.models.compute  # noqa: F401
import backend.models.network  # noqa: F401
import backend.models.orchestrator  # noqa: F401
from backend.routers import admin as admin_router
from backend.routers import user as user_router
from backend.routers import projects as projects_router
from backend.routers import agent
from sqlalchemy import text
from backend.models.db import engine, Base
from backend.routers.vm import router as vm_router

SCHEMAS = [
    "auth_service",
    "project_service",
    "compute_service",
    "network_service",
    "orchestrator",
]

with engine.begin() as conn:
    for schema in SCHEMAS:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

Base.metadata.create_all(bind=engine)

with engine.begin() as conn:
    conn.execute(text(
        "ALTER TABLE project_service.projects "
        "ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'"
    ))

app = FastAPI(title="MTS IaaS Cloud")


app.include_router(vm_router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(projects_router.router)
app.include_router(agent.router)


@app.get("/")
def root():
    return {"status": "IaaS control-plane is running"}
