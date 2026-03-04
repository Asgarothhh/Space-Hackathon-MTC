from fastapi import FastAPI
import backend.models.auth  # noqa: F401
import backend.models.projects  # noqa: F401
import backend.models.compute  # noqa: F401
import backend.models.network  # noqa: F401
import backend.models.orchestrator  # noqa: F401
from backend.routers import admin as admin_router
from backend.routers import user as user_router
from backend.routers import projects as projects_router
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

# теперь создаём таблицы в уже существующих схемах
Base.metadata.create_all(bind=engine)


app = FastAPI(title="MTS IaaS Cloud")

Base.metadata.create_all(bind=engine)


app.include_router(vm_router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(projects_router.router)


@app.get("/")
def root():
    return {"status": "IaaS control-plane is running"}
