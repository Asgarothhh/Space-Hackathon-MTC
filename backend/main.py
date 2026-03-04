from fastapi import FastAPI
from models.db import Base, engine
import models.auth
import models.projects
import models.compute
import models.network
import models.orchestrator

app = FastAPI(title="MTS IaaS Cloud")

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "IaaS control-plane is running"}
