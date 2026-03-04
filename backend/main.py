from fastapi import FastAPI

from models.db import Base, engine
import models.auth  # noqa: F401
import models.projects  # noqa: F401
import models.compute  # noqa: F401
import models.network  # noqa: F401
import models.orchestrator  # noqa: F401
from routers import admin as admin_router
from routers import user as user_router


app = FastAPI(title="MTS IaaS Cloud")

Base.metadata.create_all(bind=engine)

app.include_router(admin_router.router)
app.include_router(user_router.router)


@app.get("/")
def root():
    return {"status": "IaaS control-plane is running"}
