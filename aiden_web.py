import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from typing import Iterator
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from aiden_core import AidenEngine, DATA_ROOT, MODES


app = FastAPI(title="Aiden Web")
engine = AidenEngine()

app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

LOG_DIR = DATA_ROOT / "logs"


def _parse_positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


RATE_LIMIT_WINDOW_SECONDS = _parse_positive_int_env("AIDEN_RATE_LIMIT_WINDOW_SECONDS", 60)
RATE_LIMIT_REQUESTS_PER_WINDOW = _parse_positive_int_env("AIDEN_RATE_LIMIT_PER_WINDOW", 60)
MAX_REQUEST_BYTES = _parse_positive_int_env("AIDEN_MAX_REQUEST_BYTES", 65536)
STREAM_MAX_SECONDS = _parse_positive_int_env("AIDEN_STREAM_MAX_SECONDS", 120)
LOG_MAX_BYTES = _parse_positive_int_env("AIDEN_LOG_MAX_BYTES", 1048576)
LOG_BACKUP_COUNT = _parse_positive_int_env("AIDEN_LOG_BACKUP_COUNT", 3)


def _configure_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aiden.web")
    logger.setLevel(os.getenv("AIDEN_LOG_LEVEL", "INFO").upper())

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        LOG_DIR / "aiden-web.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s request_id=%(request_id)s client=%(client)s method=%(method)s path=%(path)s status=%(status)s duration_ms=%(duration_ms)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


WEB_LOGGER = _configure_logger()

_rate_limit_lock = threading.Lock()
_client_request_times: dict[str, deque[float]] = defaultdict(deque)
_engine_lock = threading.RLock()


def _engine_run(callable_obj, *args, **kwargs):
    with _engine_lock:
        return callable_obj(*args, **kwargs)


def _get_client_key(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown-client"


def _is_rate_limited(request: Request) -> bool:
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    key = _get_client_key(request)

    with _rate_limit_lock:
        timestamps = _client_request_times[key]
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()

        if len(timestamps) >= RATE_LIMIT_REQUESTS_PER_WINDOW:
            return True

        timestamps.append(now)
        return False


def _clear_rate_limit_state() -> None:
    with _rate_limit_lock:
        _client_request_times.clear()


def _log_api_request(
    request_id: str,
    request: Request,
    status: int,
    start_time: float,
) -> None:
    duration_ms = int((time.monotonic() - start_time) * 1000)
    WEB_LOGGER.info(
        "api-request",
        extra={
            "request_id": request_id,
            "client": _get_client_key(request),
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "duration_ms": duration_ms,
        },
    )


@app.middleware("http")
async def api_guardrails(request: Request, call_next):
    path = request.url.path
    start_time = time.monotonic()
    request_id = request.headers.get("x-request-id") or uuid4().hex
    is_api = path.startswith("/api/")

    def with_api_headers(response: JSONResponse):
        response.headers["x-request-id"] = request_id
        if is_api:
            response.headers["x-content-type-options"] = "nosniff"
            response.headers["x-frame-options"] = "DENY"
            response.headers["referrer-policy"] = "no-referrer"
            response.headers["cache-control"] = "no-store"
        return response

    if is_api and request.method in {"POST", "PUT", "PATCH"}:
        body = await request.body()
        if len(body) > MAX_REQUEST_BYTES:
            response = JSONResponse(
                {
                    "error": (
                        f"Request body too large. Max allowed is {MAX_REQUEST_BYTES} bytes."
                    )
                },
                status_code=413,
            )
            response = with_api_headers(response)
            _log_api_request(request_id, request, response.status_code, start_time)
            return response

    if is_api and _is_rate_limited(request):
        response = JSONResponse(
            {"error": "Too many requests. Please try again shortly."},
            status_code=429,
        )
        response = with_api_headers(response)
        _log_api_request(request_id, request, response.status_code, start_time)
        return response

    try:
        response = await call_next(request)
    except Exception:
        if path.startswith("/api/"):
            _log_api_request(request_id, request, 500, start_time)
        raise
    response = with_api_headers(response)
    if path.startswith("/api/"):
        _log_api_request(request_id, request, response.status_code, start_time)
    return response


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse({"error": str(exc)}, status_code=400)


@app.exception_handler(Exception)
def generic_error_handler(_: Request, exc: Exception):
    _ = exc
    return JSONResponse({"error": "Internal server error."}, status_code=500)


class ChatPayload(BaseModel):
    message: str = Field(max_length=4000)
    mode: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    short_responses: bool | None = None
    learning_style: str | None = Field(default=None, max_length=500)
    focus_goal: str | None = Field(default=None, max_length=500)
    interests: str | None = Field(default=None, max_length=500)


class ProfilePayload(BaseModel):
    name: str = Field(max_length=100)


class TaskPayload(BaseModel):
    text: str = Field(max_length=500)
    due_date: str | None = Field(default=None, max_length=10)
    priority: str | None = Field(default=None, max_length=10)


class TaskIdPayload(BaseModel):
    task_id: int


class TaskEditPayload(BaseModel):
    task_id: int
    text: str | None = Field(default=None, max_length=500)
    due_date: str | None = Field(default=None, max_length=10)
    priority: str | None = Field(default=None, max_length=10)


class TaskPostponePayload(BaseModel):
    task_id: int
    days: int = Field(default=1, ge=1, le=365)


class MemoryPayload(BaseModel):
    note: str = Field(max_length=1000)


class MemorySearchPayload(BaseModel):
    query: str = Field(max_length=500)


class ProfileImportPayload(BaseModel):
    profile_name: str = Field(max_length=100)
    profile_data: dict


def _apply_chat_preferences(payload: ChatPayload) -> None:
    with _engine_lock:
        if payload.mode:
            engine.set_mode(payload.mode)

        if payload.name and payload.name.strip():
            engine.set_name(payload.name.strip())

        if payload.short_responses is not None:
            engine.set_short_responses(payload.short_responses)

        if payload.learning_style is not None and payload.learning_style.strip():
            engine.set_learning_style(payload.learning_style)

        if payload.focus_goal is not None:
            engine.set_focus_goal(payload.focus_goal)

        if payload.interests is not None:
            engine.set_interests(payload.interests)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    prefs = _engine_run(engine.get_preferences)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "modes": list(MODES.keys()),
            "prefs": prefs,
            "profiles": _engine_run(engine.list_profiles),
            "tasks": _engine_run(engine.list_tasks),
            "memory_notes": _engine_run(engine.list_memory_notes),
            "runtime": _engine_run(engine.get_runtime_info),
        },
    )


@app.get("/health")
def health_check():
    return JSONResponse({"ok": True, "service": "aiden-web"})


@app.get("/api/state")
def get_state():
    return JSONResponse(
        {
            "prefs": _engine_run(engine.get_preferences),
            "profiles": _engine_run(engine.list_profiles),
            "tasks": _engine_run(engine.list_tasks),
            "memory_notes": _engine_run(engine.list_memory_notes),
            "runtime": _engine_run(engine.get_runtime_info),
        }
    )


@app.post("/api/runtime/retest")
def retest_runtime_model():
    runtime = _engine_run(engine.retest_model_connection)
    return JSONResponse({"ok": True, "runtime": runtime})


@app.post("/api/chat")
def chat(payload: ChatPayload):
    _apply_chat_preferences(payload)

    handled, command_output, meta = _engine_run(engine.handle_command, payload.message)
    if handled:
        return JSONResponse(
            {
                "answer": command_output,
                "prefs": _engine_run(engine.get_preferences),
                "meta": meta,
                "runtime": _engine_run(engine.get_runtime_info),
            }
        )

    answer = _engine_run(engine.chat, payload.message)
    prefs = _engine_run(engine.get_preferences)
    return JSONResponse(
        {
            "answer": answer,
            "prefs": prefs,
            "meta": {"type": "chat"},
            "runtime": _engine_run(engine.get_runtime_info),
        }
    )


@app.post("/api/chat/stream")
def chat_stream(payload: ChatPayload):
    _apply_chat_preferences(payload)

    def iter_lines() -> Iterator[str]:
        with _engine_lock:
            try:
                handled, command_output, meta = engine.handle_command(payload.message)
                if handled:
                    if command_output:
                        yield json.dumps({"type": "chunk", "text": command_output}) + "\n"
                    yield (
                        json.dumps(
                            {
                                "type": "final",
                                "prefs": engine.get_preferences(),
                                "meta": meta,
                                "runtime": engine.get_runtime_info(),
                            }
                        )
                        + "\n"
                    )
                    return

                start_time = time.monotonic()
                for part in engine.chat_stream(payload.message):
                    if time.monotonic() - start_time > STREAM_MAX_SECONDS:
                        raise TimeoutError(
                            f"Streaming response exceeded {STREAM_MAX_SECONDS} seconds."
                        )
                    if part:
                        yield json.dumps({"type": "chunk", "text": part}) + "\n"

                yield (
                    json.dumps(
                        {
                            "type": "final",
                            "prefs": engine.get_preferences(),
                            "meta": {"type": "chat"},
                            "runtime": engine.get_runtime_info(),
                        }
                    )
                    + "\n"
                )
            except Exception as exc:
                yield json.dumps({"type": "error", "error": str(exc)}) + "\n"
                yield (
                    json.dumps(
                        {
                            "type": "final",
                            "prefs": engine.get_preferences(),
                            "meta": {"type": "error"},
                            "runtime": engine.get_runtime_info(),
                        }
                    )
                    + "\n"
                )

    return StreamingResponse(iter_lines(), media_type="application/x-ndjson")


@app.post("/api/reset")
def reset_chat():
    _engine_run(engine.reset_chat)
    return JSONResponse({"ok": True, "message": "Conversation context reset."})


@app.post("/api/export")
def export_chat():
    path = _engine_run(engine.export_chat)
    return JSONResponse({"ok": True, "path": str(path)})


@app.post("/api/profiles/create")
def profile_create(payload: ProfilePayload):
    created = _engine_run(engine.create_profile, payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Profile created: {created}",
            "prefs": _engine_run(engine.get_preferences),
            "profiles": _engine_run(engine.list_profiles),
        }
    )


@app.post("/api/profiles/switch")
def profile_switch(payload: ProfilePayload):
    switched = _engine_run(engine.switch_profile, payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Switched to profile: {switched}",
            "prefs": _engine_run(engine.get_preferences),
            "profiles": _engine_run(engine.list_profiles),
            "tasks": _engine_run(engine.list_tasks),
            "memory_notes": _engine_run(engine.list_memory_notes),
        }
    )


@app.post("/api/profiles/delete")
def profile_delete(payload: ProfilePayload):
    deleted = _engine_run(engine.delete_profile, payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Deleted profile: {deleted}",
            "prefs": _engine_run(engine.get_preferences),
            "profiles": _engine_run(engine.list_profiles),
            "tasks": _engine_run(engine.list_tasks),
            "memory_notes": _engine_run(engine.list_memory_notes),
        }
    )


@app.post("/api/profiles/export")
def profile_export():
    path = _engine_run(engine.export_active_profile)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JSONResponse({"ok": True, "path": str(path), "payload": payload})


@app.post("/api/profiles/import")
def profile_import(payload: ProfileImportPayload):
    imported = _engine_run(engine.import_profile_from_json, payload.profile_name, payload.profile_data)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Imported profile: {imported}",
            "prefs": _engine_run(engine.get_preferences),
            "profiles": _engine_run(engine.list_profiles),
            "tasks": _engine_run(engine.list_tasks),
            "memory_notes": _engine_run(engine.list_memory_notes),
        }
    )


@app.get("/api/tasks")
def task_list():
    return JSONResponse({"tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/add")
def task_add(payload: TaskPayload):
    task = _engine_run(
        engine.add_task,
        payload.text,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    return JSONResponse({"ok": True, "task": task, "tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/done")
def task_done(payload: TaskIdPayload):
    task = _engine_run(engine.complete_task, payload.task_id)
    return JSONResponse({"ok": True, "task": task, "tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/edit")
def task_edit(payload: TaskEditPayload):
    task = _engine_run(
        engine.edit_task,
        payload.task_id,
        text=payload.text,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    return JSONResponse({"ok": True, "task": task, "tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/postpone")
def task_postpone(payload: TaskPostponePayload):
    task = _engine_run(engine.postpone_task, payload.task_id, days=payload.days)
    return JSONResponse({"ok": True, "task": task, "tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/remove")
def task_remove(payload: TaskIdPayload):
    _engine_run(engine.remove_task, payload.task_id)
    return JSONResponse({"ok": True, "tasks": _engine_run(engine.list_tasks)})


@app.post("/api/tasks/clear")
def task_clear():
    _engine_run(engine.clear_tasks)
    return JSONResponse({"ok": True, "tasks": _engine_run(engine.list_tasks)})


@app.get("/api/memory")
def memory_list():
    return JSONResponse({"memory_notes": _engine_run(engine.list_memory_notes)})


@app.post("/api/memory/add")
def memory_add(payload: MemoryPayload):
    note = _engine_run(engine.add_memory_note, payload.note)
    return JSONResponse(
        {
            "ok": True,
            "note": note,
            "memory_notes": _engine_run(engine.list_memory_notes),
        }
    )


@app.post("/api/memory/clear")
def memory_clear():
    _engine_run(engine.clear_memory_notes)
    return JSONResponse({"ok": True, "memory_notes": _engine_run(engine.list_memory_notes)})


@app.post("/api/memory/search")
def memory_search(payload: MemorySearchPayload):
    results = _engine_run(engine.recall_memory_notes, payload.query, limit=10)
    return JSONResponse({"ok": True, "results": results})
