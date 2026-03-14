import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from aiden_core import AidenEngine, MODES


app = FastAPI(title="Aiden Web")
engine = AidenEngine()

app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


class ChatPayload(BaseModel):
    message: str
    mode: str | None = None
    name: str | None = None
    short_responses: bool | None = None
    learning_style: str | None = None
    focus_goal: str | None = None
    interests: str | None = None


class ProfilePayload(BaseModel):
    name: str


class TaskPayload(BaseModel):
    text: str
    due_date: str | None = None
    priority: str | None = None


class TaskIdPayload(BaseModel):
    task_id: int


class TaskEditPayload(BaseModel):
    task_id: int
    text: str | None = None
    due_date: str | None = None
    priority: str | None = None


class TaskPostponePayload(BaseModel):
    task_id: int
    days: int = 1


class MemoryPayload(BaseModel):
    note: str


class MemorySearchPayload(BaseModel):
    query: str


class ProfileImportPayload(BaseModel):
    profile_name: str
    profile_data: dict


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    prefs = engine.get_preferences()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "modes": list(MODES.keys()),
            "prefs": prefs,
            "profiles": engine.list_profiles(),
            "tasks": engine.list_tasks(),
            "memory_notes": engine.list_memory_notes(),
            "runtime": engine.get_runtime_info(),
        },
    )


@app.get("/health")
def health_check():
    return JSONResponse({"ok": True, "service": "aiden-web"})


@app.get("/api/state")
def get_state():
    return JSONResponse(
        {
            "prefs": engine.get_preferences(),
            "profiles": engine.list_profiles(),
            "tasks": engine.list_tasks(),
            "memory_notes": engine.list_memory_notes(),
            "runtime": engine.get_runtime_info(),
        }
    )


@app.post("/api/chat")
def chat(payload: ChatPayload):
    try:
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

        handled, command_output, meta = engine.handle_command(payload.message)
        if handled:
            return JSONResponse(
                {
                    "answer": command_output,
                    "prefs": engine.get_preferences(),
                    "meta": meta,
                    "runtime": engine.get_runtime_info(),
                }
            )

        answer = engine.chat(payload.message)
        prefs = engine.get_preferences()
        return JSONResponse(
            {
                "answer": answer,
                "prefs": prefs,
                "meta": {"type": "chat"},
                "runtime": engine.get_runtime_info(),
            }
        )
    except Exception as exc:
        return JSONResponse(
            {"error": str(exc)},
            status_code=400,
        )


@app.post("/api/reset")
def reset_chat():
    engine.reset_chat()
    return JSONResponse({"ok": True, "message": "Conversation context reset."})


@app.post("/api/export")
def export_chat():
    path = engine.export_chat()
    return JSONResponse({"ok": True, "path": str(path)})


@app.post("/api/profiles/create")
def profile_create(payload: ProfilePayload):
    created = engine.create_profile(payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Profile created: {created}",
            "prefs": engine.get_preferences(),
            "profiles": engine.list_profiles(),
        }
    )


@app.post("/api/profiles/switch")
def profile_switch(payload: ProfilePayload):
    switched = engine.switch_profile(payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Switched to profile: {switched}",
            "prefs": engine.get_preferences(),
            "profiles": engine.list_profiles(),
            "tasks": engine.list_tasks(),
            "memory_notes": engine.list_memory_notes(),
        }
    )


@app.post("/api/profiles/delete")
def profile_delete(payload: ProfilePayload):
    deleted = engine.delete_profile(payload.name)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Deleted profile: {deleted}",
            "prefs": engine.get_preferences(),
            "profiles": engine.list_profiles(),
            "tasks": engine.list_tasks(),
            "memory_notes": engine.list_memory_notes(),
        }
    )


@app.post("/api/profiles/export")
def profile_export():
    path = engine.export_active_profile()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JSONResponse({"ok": True, "path": str(path), "payload": payload})


@app.post("/api/profiles/import")
def profile_import(payload: ProfileImportPayload):
    imported = engine.import_profile_from_json(payload.profile_name, payload.profile_data)
    return JSONResponse(
        {
            "ok": True,
            "message": f"Imported profile: {imported}",
            "prefs": engine.get_preferences(),
            "profiles": engine.list_profiles(),
            "tasks": engine.list_tasks(),
            "memory_notes": engine.list_memory_notes(),
        }
    )


@app.get("/api/tasks")
def task_list():
    return JSONResponse({"tasks": engine.list_tasks()})


@app.post("/api/tasks/add")
def task_add(payload: TaskPayload):
    task = engine.add_task(
        payload.text,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    return JSONResponse({"ok": True, "task": task, "tasks": engine.list_tasks()})


@app.post("/api/tasks/done")
def task_done(payload: TaskIdPayload):
    task = engine.complete_task(payload.task_id)
    return JSONResponse({"ok": True, "task": task, "tasks": engine.list_tasks()})


@app.post("/api/tasks/edit")
def task_edit(payload: TaskEditPayload):
    task = engine.edit_task(
        payload.task_id,
        text=payload.text,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    return JSONResponse({"ok": True, "task": task, "tasks": engine.list_tasks()})


@app.post("/api/tasks/postpone")
def task_postpone(payload: TaskPostponePayload):
    task = engine.postpone_task(payload.task_id, days=payload.days)
    return JSONResponse({"ok": True, "task": task, "tasks": engine.list_tasks()})


@app.post("/api/tasks/remove")
def task_remove(payload: TaskIdPayload):
    engine.remove_task(payload.task_id)
    return JSONResponse({"ok": True, "tasks": engine.list_tasks()})


@app.post("/api/tasks/clear")
def task_clear():
    engine.clear_tasks()
    return JSONResponse({"ok": True, "tasks": engine.list_tasks()})


@app.get("/api/memory")
def memory_list():
    return JSONResponse({"memory_notes": engine.list_memory_notes()})


@app.post("/api/memory/add")
def memory_add(payload: MemoryPayload):
    note = engine.add_memory_note(payload.note)
    return JSONResponse(
        {
            "ok": True,
            "note": note,
            "memory_notes": engine.list_memory_notes(),
        }
    )


@app.post("/api/memory/clear")
def memory_clear():
    engine.clear_memory_notes()
    return JSONResponse({"ok": True, "memory_notes": engine.list_memory_notes()})


@app.post("/api/memory/search")
def memory_search(payload: MemorySearchPayload):
    results = engine.recall_memory_notes(payload.query, limit=10)
    return JSONResponse({"ok": True, "results": results})
