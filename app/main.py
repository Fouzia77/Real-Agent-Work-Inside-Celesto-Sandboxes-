
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from . import ledger
from .celesto_executor import new_sandbox_name
from .agent import run_proof_task

NAME_RE = re.compile(r"^sbx-[a-z0-9]{8,}$")
VALID_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry briefly so startup remains resilient if Postgres is just becoming available.
    last_error = None
    for _ in range(30):
        try:
            ledger.init_db()
            break
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    else:
        raise RuntimeError(f"Could not initialize ledger: {last_error}")
    yield

app = FastAPI(title="Celesto Agent Flight Recorder", version="1.0.0", lifespan=lifespan)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": str(error.get("msg", "Invalid request")),
            "type": str(error.get("type", "value_error")),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": errors})


class RunCreate(BaseModel):
    run_id: str = Field(min_length=1, max_length=128)
    sandbox_name: str
    problem_id: str = Field(min_length=1, max_length=128)
    state: str
    execution_target: str

    @field_validator("sandbox_name")
    @classmethod
    def valid_name(cls, value):
        if not NAME_RE.fullmatch(value):
            raise ValueError("sandbox_name must match sbx- plus 8 or more lowercase letters/digits")
        return value

    @field_validator("state")
    @classmethod
    def valid_state(cls, value):
        if value not in VALID_STATES:
            raise ValueError("unknown state")
        return value

    @field_validator("execution_target")
    @classmethod
    def valid_target(cls, value):
        if value != "celesto_sandbox":
            raise ValueError("execution_target must be celesto_sandbox")
        return value

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/runs")
def get_runs():
    try:
        return ledger.list_runs()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ledger unavailable: {type(exc).__name__}")

@app.post("/api/runs", status_code=201)
def post_run(item: RunCreate):
    try:
        return ledger.create_run(item.model_dump())
    except Exception as exc:
        if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="run_id already exists")
        raise HTTPException(status_code=503, detail=f"ledger unavailable: {type(exc).__name__}")

@app.post("/api/agent/proof")
def execute_proof(inject_attack: bool = False):
    try:
        result = run_proof_task(inject_attack=inject_attack)
        payload = {
            "run_id": f"run-{uuid.uuid4().hex}",
            "sandbox_name": result["sandbox_name"],
            "problem_id": "proof-file-verification",
            "state": "succeeded" if result["success"] else "failed",
            "execution_target": "celesto_sandbox",
        }
        ledger.create_run(payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Celesto task failed: {type(exc).__name__}: {exc}")
