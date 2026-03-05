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
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse




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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("VALIDATION ERROR:", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.include_router(vm_router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(projects_router.router)
app.include_router(agent.router, prefix='/agent')


@app.get("/")
def root():
    return {"status": "IaaS control-plane is running"}