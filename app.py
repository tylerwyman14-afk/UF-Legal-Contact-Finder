import csv
import io
import os
import socket
import subprocess
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.db import (
    init_db, list_people, get_person, upsert_person, delete_person, distinct_filters,
)

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"


def load_config():
    with open(BASE_DIR / "config.yaml") as f:
        return yaml.safe_load(f)


def _kill_stale_port(port: int):
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="UF Alumni Legal Finder", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


class PersonIn(BaseModel):
    full_name: str
    title: str
    organization: str
    org_type: str
    practice_area: str | None = None
    city: str | None = None
    state: str | None = None
    uf_degree: str | None = None
    uf_grad_year: int | None = None
    email: str | None = None
    phone: str | None = None
    contact_form_url: str | None = None
    linkedin_url: str | None = None
    source_url: str
    source_note: str | None = None
    date_verified: str
    confidence: str = "verified"
    notes: str | None = None


@app.get("/")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/people")
async def api_list_people(q: str = None, org_type: str = None, practice_area: str = None,
                           state: str = None, limit: int = 200, offset: int = 0):
    return list_people(q=q, org_type=org_type, practice_area=practice_area, state=state,
                        limit=limit, offset=offset)


@app.get("/api/people/export.csv")
async def api_export_csv(q: str = None, org_type: str = None, practice_area: str = None,
                          state: str = None):
    rows = list_people(q=q, org_type=org_type, practice_area=practice_area, state=state, limit=10000)
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=uf_alumni_legal_contacts.csv"},
    )


@app.get("/api/meta/filters")
async def api_filters():
    return distinct_filters()


@app.get("/api/people/{person_id}")
async def api_get_person(person_id: int):
    person = get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Not found")
    return person


@app.post("/api/people")
async def api_create_person(person: PersonIn):
    person_id = upsert_person(person.model_dump())
    return get_person(person_id)


@app.put("/api/people/{person_id}")
async def api_update_person(person_id: int, person: PersonIn):
    existing = get_person(person_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    data = person.model_dump()
    upsert_person(data)
    return get_person(person_id)


@app.delete("/api/people/{person_id}")
async def api_delete_person(person_id: int):
    if not delete_person(person_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


if __name__ == "__main__":
    cfg = load_config()
    host = cfg.get("server", {}).get("host", "127.0.0.1")
    port = cfg.get("server", {}).get("port", 8080)
    _kill_stale_port(port)
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=False)
