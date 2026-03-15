import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

ROOT = Path(__file__).resolve().parent


def _resolve_data_root(raw_value: str | None) -> Path:
    value = (raw_value or "").strip()
    if not value:
        return ROOT
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


DATA_ROOT = _resolve_data_root(os.getenv("AIDEN_DATA_DIR"))

PREFERENCES_FILE = DATA_ROOT / "preferences.json"
PROFILES_FILE = DATA_ROOT / "profiles.json"
AIDEN_PROMPT_FILE = ROOT / "aiden_prompt.md"
CHAT_EXPORT_DIR = DATA_ROOT / "chat_exports"
PROFILE_EXPORT_DIR = DATA_ROOT / "profile_exports"

MODES: Dict[str, str] = {
    "study": "Study Mode",
    "coding": "Coding Mode",
    "idea": "Idea Mode",
    "productivity": "Productivity Mode",
}

SAFETY_BLOCKLIST = [
    "make a bomb",
    "build a bomb",
    "hack into",
    "steal password",
    "credit card fraud",
    "malware",
    "ransomware",
    "how to kill",
    "illegal drugs",
]


class AidenEngine:
    def __init__(self) -> None:
        load_dotenv()

        # Resolve data paths at construction time so each instance is isolated.
        data_root = _resolve_data_root(os.getenv("AIDEN_DATA_DIR"))
        self.profiles_file = data_root / "profiles.json"
        self.preferences_file = data_root / "preferences.json"
        self.chat_export_dir = data_root / "chat_exports"
        self.profile_export_dir = data_root / "profile_exports"

        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AIDEN_MODEL", "gpt-5.3-codex")
        self.max_messages = self._parse_max_messages(os.getenv("AIDEN_MAX_MESSAGES"))
        self.dev_mode = os.getenv("AIDEN_DEV_MODE", "true").lower() != "false"
        self.client: OpenAI | None = None
        self.model_healthy = False
        self.last_model_error = ""

        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.model_healthy = True
        elif not self.dev_mode:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and set your key, "
                "or enable AIDEN_DEV_MODE=true."
            )

        self.profile_store = self.load_profile_store()
        self.active_profile = self.profile_store["active_profile"]
        self.preferences = self.profile_store["profiles"][self.active_profile]
        self.base_prompt = self.load_aiden_base_prompt()

        self.messages: List[Dict[str, str]] = []
        self.refresh_system_prompt()

    @staticmethod
    def _default_preferences() -> Dict[str, object]:
        return {
            "name": "User",
            "mode": "study",
            "short_responses": "false",
            "learning_style": "step-by-step",
            "focus_goal": "",
            "interests": "",
            "tasks": [],
            "memory_notes": [],
        }

    @staticmethod
    def _sanitize_profile(preferences: Dict[str, object] | object) -> Dict[str, object]:
        merged = AidenEngine._default_preferences()
        if isinstance(preferences, dict):
            merged.update(preferences)

        mode = str(merged.get("mode", "study")).lower()
        if mode not in MODES:
            mode = "study"

        short_responses = str(merged.get("short_responses", "false")).lower()
        if short_responses not in {"true", "false"}:
            short_responses = "false"

        tasks = merged.get("tasks", [])
        memory_notes = merged.get("memory_notes", [])

        sanitized: Dict[str, object] = {
            "name": str(merged.get("name", "User")).strip() or "User",
            "mode": mode,
            "short_responses": short_responses,
            "learning_style": str(merged.get("learning_style", "step-by-step"))
            .strip()
            or "step-by-step",
            "focus_goal": str(merged.get("focus_goal", "")).strip(),
            "interests": str(merged.get("interests", "")).strip(),
            "tasks": tasks if isinstance(tasks, list) else [],
            "memory_notes": memory_notes if isinstance(memory_notes, list) else [],
        }

        return sanitized

    @staticmethod
    def _parse_max_messages(raw_value: str | None) -> int:
        try:
            value = int((raw_value or "30").strip())
        except ValueError:
            return 30
        return max(5, value)

    def load_preferences(self) -> Dict[str, str]:
        default = self._default_preferences()
        if not self.preferences_file.exists():
            return default
        try:
            loaded = json.loads(self.preferences_file.read_text(encoding="utf-8"))
            return self._sanitize_profile(loaded)
        except (json.JSONDecodeError, OSError):
            return default

    def save_preferences(self, preferences: Dict[str, str]) -> None:
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
        self.preferences_file.write_text(
            json.dumps(preferences, indent=2),
            encoding="utf-8",
        )

    def load_profile_store(self) -> Dict[str, object]:
        if self.profiles_file.exists():
            try:
                loaded = json.loads(self.profiles_file.read_text(encoding="utf-8"))
                profiles = loaded.get("profiles", {})
                active_profile = loaded.get("active_profile", "default")
                if not isinstance(profiles, dict) or not profiles:
                    raise ValueError("Invalid profiles store")
                sanitized_profiles = {
                    str(name).strip().lower().replace(" ", "-"): self._sanitize_profile(profile)
                    for name, profile in profiles.items()
                    if str(name).strip()
                }
                if not sanitized_profiles:
                    raise ValueError("Invalid profiles store")
                profiles = sanitized_profiles
                if active_profile not in profiles:
                    active_profile = next(iter(profiles.keys()))
                return {"active_profile": active_profile, "profiles": profiles}
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        legacy = self.load_preferences()
        initial = {
            "active_profile": "default",
            "profiles": {
                "default": legacy,
            },
        }
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
        self.profiles_file.write_text(json.dumps(initial, indent=2), encoding="utf-8")
        return initial

    def save_profile_store(self) -> None:
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
        self.profiles_file.write_text(
            json.dumps(self.profile_store, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def load_aiden_base_prompt() -> str:
        if not AIDEN_PROMPT_FILE.exists():
            raise FileNotFoundError("aiden_prompt.md not found.")
        return AIDEN_PROMPT_FILE.read_text(encoding="utf-8").strip()

    @staticmethod
    def is_unsafe_prompt(user_text: str) -> bool:
        lowered = user_text.lower()
        return any(term in lowered for term in SAFETY_BLOCKLIST)

    @staticmethod
    def mode_instruction(mode: str) -> str:
        if mode == "study":
            return (
                "You are in Study Mode. Teach step-by-step and include simple examples "
                "to build understanding."
            )
        if mode == "coding":
            return (
                "You are in Coding Mode. Provide practical code examples, debugging steps, "
                "and explain trade-offs briefly."
            )
        if mode == "idea":
            return (
                "You are in Idea Mode. Generate creative, feasible ideas with clear next actions."
            )
        if mode == "productivity":
            return (
                "You are in Productivity Mode. Prioritize action plans, schedules, and "
                "decision clarity."
            )
        return ""

    def build_system_prompt(self) -> str:
        mode = self.preferences.get("mode", "study").lower()
        short_responses = (
            self.preferences.get("short_responses", "false").lower() == "true"
        )

        parts = [self.base_prompt, self.mode_instruction(mode)]

        if short_responses:
            parts.append("Prefer concise answers unless the user asks for detail.")

        name = self.preferences.get("name", "User")
        parts.append(
            f"Remember known user preference: name is {name}. Use it naturally and sparingly."
        )

        learning_style = self.preferences.get("learning_style", "step-by-step")
        parts.append(f"Preferred learning style: {learning_style}.")

        goal = self.preferences.get("focus_goal", "").strip()
        if goal:
            parts.append(f"Current focus goal: {goal}.")

        interests = self.preferences.get("interests", "").strip()
        if interests:
            parts.append(f"Known interests: {interests}.")

        notes = self.preferences.get("memory_notes", [])
        if notes:
            recent_notes = notes[-3:]
            parts.append(
                "Known user notes: " + " | ".join(str(note) for note in recent_notes)
            )

        return "\n\n".join(part for part in parts if part)

    def refresh_system_prompt(self) -> None:
        system_prompt = self.build_system_prompt()
        if not self.messages:
            self.messages = [{"role": "system", "content": system_prompt}]
            return
        self.messages[0] = {"role": "system", "content": system_prompt}

    def set_mode(self, mode: str) -> str:
        mode = mode.lower()
        if mode not in MODES:
            raise ValueError("Invalid mode. Use: study, coding, idea, productivity")
        self.preferences["mode"] = mode
        self.save_profile_store()
        self.refresh_system_prompt()
        return MODES[mode]

    def set_name(self, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise ValueError("Name cannot be empty.")
        self.preferences["name"] = clean
        self.save_profile_store()
        self.refresh_system_prompt()
        return clean

    def set_short_responses(self, enabled: bool) -> None:
        self.preferences["short_responses"] = "true" if enabled else "false"
        self.save_profile_store()
        self.refresh_system_prompt()

    def set_learning_style(self, learning_style: str) -> str:
        clean = learning_style.strip()
        if not clean:
            raise ValueError("Learning style cannot be empty.")
        self.preferences["learning_style"] = clean
        self.save_profile_store()
        self.refresh_system_prompt()
        return clean

    def set_focus_goal(self, focus_goal: str) -> str:
        clean = focus_goal.strip()
        self.preferences["focus_goal"] = clean
        self.save_profile_store()
        self.refresh_system_prompt()
        return clean

    def set_interests(self, interests: str) -> str:
        clean = interests.strip()
        self.preferences["interests"] = clean
        self.save_profile_store()
        self.refresh_system_prompt()
        return clean

    def list_profiles(self) -> List[str]:
        return list(self.profile_store["profiles"].keys())

    def create_profile(self, profile_name: str) -> str:
        name = profile_name.strip().lower().replace(" ", "-")
        if not name:
            raise ValueError("Profile name cannot be empty.")
        profiles = self.profile_store["profiles"]
        if name in profiles:
            raise ValueError(f"Profile already exists: {name}")
        profiles[name] = self._default_preferences()
        self.save_profile_store()
        return name

    def switch_profile(self, profile_name: str) -> str:
        name = profile_name.strip().lower().replace(" ", "-")
        profiles = self.profile_store["profiles"]
        if name not in profiles:
            raise ValueError(f"Unknown profile: {name}")
        self.profile_store["active_profile"] = name
        self.active_profile = name
        self.preferences = profiles[name]
        self.save_profile_store()
        self.reset_chat()
        return name

    def delete_profile(self, profile_name: str) -> str:
        name = profile_name.strip().lower().replace(" ", "-")
        profiles = self.profile_store["profiles"]
        if name not in profiles:
            raise ValueError(f"Unknown profile: {name}")
        if len(profiles) == 1:
            raise ValueError("Cannot delete the only profile.")
        del profiles[name]
        if self.active_profile == name:
            self.active_profile = next(iter(profiles.keys()))
            self.profile_store["active_profile"] = self.active_profile
            self.preferences = profiles[self.active_profile]
            self.reset_chat()
        self.save_profile_store()
        return name

    def _next_task_id(self) -> int:
        tasks = self.preferences.get("tasks", [])
        if not tasks:
            return 1
        return max(int(t.get("id", 0)) for t in tasks) + 1

    @staticmethod
    def _normalize_priority(priority: str | None) -> str:
        value = (priority or "medium").strip().lower()
        if value not in {"low", "medium", "high"}:
            raise ValueError("Priority must be one of: low, medium, high")
        return value

    @staticmethod
    def _normalize_due_date(due_date: str | None) -> str:
        value = (due_date or "").strip()
        if not value:
            return ""
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Due date must be in YYYY-MM-DD format") from exc
        return value

    def add_task(
        self, text: str, due_date: str | None = None, priority: str | None = None
    ) -> Dict[str, object]:
        clean = text.strip()
        if not clean:
            raise ValueError("Task text cannot be empty.")
        task = {
            "id": self._next_task_id(),
            "text": clean,
            "done": False,
            "priority": self._normalize_priority(priority),
            "due_date": self._normalize_due_date(due_date),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.preferences.setdefault("tasks", []).append(task)
        self.save_profile_store()
        return task

    def list_tasks(self) -> List[Dict[str, object]]:
        raw_tasks = list(self.preferences.get("tasks", []))

        def score(task: Dict[str, object]) -> Tuple[int, str, int]:
            done_flag = 1 if task.get("done") else 0
            due = str(task.get("due_date", "") or "")
            due_key = due if due else "9999-12-31"
            priority = str(task.get("priority", "medium"))
            priority_rank = {"high": 0, "medium": 1, "low": 2}.get(priority, 1)
            return (done_flag, due_key, priority_rank)

        normalized: List[Dict[str, object]] = []
        for task in raw_tasks:
            copy = dict(task)
            copy["priority"] = str(copy.get("priority", "medium"))
            copy["due_date"] = str(copy.get("due_date", ""))
            normalized.append(copy)

        normalized.sort(key=score)
        return normalized

    def complete_task(self, task_id: int) -> Dict[str, object]:
        for task in self.preferences.get("tasks", []):
            if int(task.get("id", -1)) == task_id:
                task["done"] = True
                self.save_profile_store()
                return task
        raise ValueError(f"Task not found: {task_id}")

    def edit_task(
        self,
        task_id: int,
        text: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
    ) -> Dict[str, object]:
        for task in self.preferences.get("tasks", []):
            if int(task.get("id", -1)) != task_id:
                continue
            if text is not None:
                clean_text = text.strip()
                if not clean_text:
                    raise ValueError("Task text cannot be empty.")
                task["text"] = clean_text
            if due_date is not None:
                task["due_date"] = self._normalize_due_date(due_date)
            if priority is not None:
                task["priority"] = self._normalize_priority(priority)
            self.save_profile_store()
            return dict(task)
        raise ValueError(f"Task not found: {task_id}")

    def postpone_task(self, task_id: int, days: int = 1) -> Dict[str, object]:
        if days < 1:
            raise ValueError("Postpone days must be at least 1")
        for task in self.preferences.get("tasks", []):
            if int(task.get("id", -1)) != task_id:
                continue
            due_raw = str(task.get("due_date", "") or "")
            base_date = datetime.now().date()
            if due_raw:
                base_date = datetime.strptime(due_raw, "%Y-%m-%d").date()
            task["due_date"] = (base_date + timedelta(days=days)).isoformat()
            self.save_profile_store()
            return dict(task)
        raise ValueError(f"Task not found: {task_id}")

    def remove_task(self, task_id: int) -> None:
        tasks = self.preferences.get("tasks", [])
        filtered = [t for t in tasks if int(t.get("id", -1)) != task_id]
        if len(filtered) == len(tasks):
            raise ValueError(f"Task not found: {task_id}")
        self.preferences["tasks"] = filtered
        self.save_profile_store()

    def clear_tasks(self) -> None:
        self.preferences["tasks"] = []
        self.save_profile_store()

    def add_memory_note(self, note: str) -> str:
        clean = note.strip()
        if not clean:
            raise ValueError("Memory note cannot be empty.")
        notes = self.preferences.setdefault("memory_notes", [])
        notes.append(clean)
        if len(notes) > 100:
            self.preferences["memory_notes"] = notes[-100:]
        self.save_profile_store()
        self.refresh_system_prompt()
        return clean

    def list_memory_notes(self) -> List[str]:
        return list(self.preferences.get("memory_notes", []))

    def clear_memory_notes(self) -> None:
        self.preferences["memory_notes"] = []
        self.save_profile_store()
        self.refresh_system_prompt()

    def export_active_profile(self) -> Path:
        self.profile_export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.profile_export_dir / f"profile_{self.active_profile}_{stamp}.json"
        payload = {
            "profile_name": self.active_profile,
            "profile": dict(self.preferences),
            "exported_at": datetime.now().isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def import_profile_from_json(self, profile_name: str, profile_data: Dict[str, object]) -> str:
        name = profile_name.strip().lower().replace(" ", "-")
        if not name:
            raise ValueError("Profile name cannot be empty.")

        self.profile_store["profiles"][name] = self._sanitize_profile(profile_data)
        self.profile_store["active_profile"] = name
        self.active_profile = name
        self.preferences = self.profile_store["profiles"][name]
        self.save_profile_store()
        self.reset_chat()
        return name

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))

    def recall_memory_notes(self, query: str, limit: int = 3) -> List[str]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        scored: List[Tuple[int, str]] = []
        for note in self.preferences.get("memory_notes", []):
            note_tokens = self._tokenize(str(note))
            score = len(query_tokens & note_tokens)
            if score > 0:
                scored.append((score, str(note)))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [note for _, note in scored[:limit]]

    def get_preferences(self) -> Dict[str, str]:
        payload = dict(self.preferences)
        payload["active_profile"] = self.active_profile
        return payload

    def get_runtime_info(self) -> Dict[str, object]:
        configured_model = self.client is not None
        has_model = configured_model and self.model_healthy
        mode_label = "live" if has_model else ("local-fallback" if configured_model else "local")
        payload: Dict[str, object] = {
            "dev_mode": self.dev_mode,
            "has_model": has_model,
            "mode_label": mode_label,
        }
        if self.last_model_error:
            payload["model_error"] = self.last_model_error
        return payload

    def retest_model_connection(self) -> Dict[str, object]:
        if self.client is None:
            self.model_healthy = False
            self.last_model_error = "OPENAI_API_KEY is not configured."
            return self.get_runtime_info()

        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                temperature=0,
                max_tokens=1,
            )
            self.model_healthy = True
            self.last_model_error = ""
        except Exception as exc:
            self.model_healthy = False
            self.last_model_error = (
                f"Model connection test failed ({type(exc).__name__}): {exc}."
            )

        return self.get_runtime_info()

    def get_help_text(self) -> str:
        return (
            "Commands:\n"
            "  /help\n"
            "  /mode <study|coding|idea|productivity>\n"
            "  /name <your_name>\n"
            "  /short <on|off>\n"
            "  /style <learning_style>\n"
            "  /goal <focus_goal>\n"
            "  /interests <comma separated interests>\n"
            "  /profiles\n"
            "  /profile create <name>\n"
            "  /profile switch <name>\n"
            "  /profile delete <name>\n"
            "  /profile export\n"
            "  /task add <text>\n"
            "  /task list\n"
            "  /task done <id>\n"
            "  /task edit <id>|<text>|<priority>|<YYYY-MM-DD>\n"
            "  /task postpone <id> [days]\n"
            "  /task remove <id>\n"
            "  /task clear\n"
            "  /memory add <note>\n"
            "  /memory list\n"
            "  /memory clear\n"
            "  /memory recall <query>\n"
            "  /prefs\n"
            "  /reset\n"
            "  /export [filename]\n"
            "  /exit"
        )

    def get_chat_transcript(self) -> List[Dict[str, str]]:
        return [m for m in self.messages[1:]]

    def reset_chat(self) -> None:
        self.messages = []
        self.refresh_system_prompt()

    def export_chat(self, file_stem: str = "") -> Path:
        self.chat_export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = file_stem.strip().replace(" ", "_") if file_stem else f"aiden_chat_{stamp}"
        export_path = self.chat_export_dir / f"{stem}.md"

        lines = [
            "# Aiden Chat Export",
            "",
            f"- Exported at: {datetime.now().isoformat(timespec='seconds')}",
            f"- Profile: {self.active_profile}",
            f"- Mode: {self.preferences.get('mode', 'study')}",
            f"- Name: {self.preferences.get('name', 'User')}",
            "",
        ]

        for msg in self.get_chat_transcript():
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            lines.append(f"## {role}")
            lines.append("")
            lines.append(content)
            lines.append("")

        export_path.write_text("\n".join(lines), encoding="utf-8")
        return export_path

    def _trim_messages(self) -> None:
        if len(self.messages) <= self.max_messages + 1:
            return
        keep = self.messages[-self.max_messages :]
        self.messages = [self.messages[0], *keep]

    def handle_command(self, user_text: str) -> Tuple[bool, str, Dict[str, str]]:
        if not user_text.startswith("/"):
            return (False, "", {})

        parts = user_text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/help":
            return (True, self.get_help_text(), {"type": "help"})

        if cmd == "/mode":
            mode_name = self.set_mode(arg)
            return (True, f"Mode switched to {mode_name}.", {"type": "prefs"})

        if cmd == "/name":
            saved = self.set_name(arg)
            return (True, f"Saved preferred name: {saved}", {"type": "prefs"})

        if cmd == "/short":
            value = arg.lower()
            if value not in {"on", "off"}:
                raise ValueError("Usage: /short <on|off>")
            self.set_short_responses(value == "on")
            state = "enabled" if value == "on" else "disabled"
            return (
                True,
                f"Concise response preference {state}.",
                {"type": "prefs"},
            )

        if cmd == "/style":
            style = self.set_learning_style(arg)
            return (True, f"Learning style set to: {style}", {"type": "prefs"})

        if cmd == "/goal":
            goal = self.set_focus_goal(arg)
            return (True, f"Focus goal updated: {goal or '(cleared)'}", {"type": "prefs"})

        if cmd == "/interests":
            interests = self.set_interests(arg)
            return (
                True,
                f"Interests updated: {interests or '(cleared)'}",
                {"type": "prefs"},
            )

        if cmd == "/profiles":
            all_profiles = self.list_profiles()
            lines = ["Profiles:"]
            for p in all_profiles:
                marker = " (active)" if p == self.active_profile else ""
                lines.append(f"  - {p}{marker}")
            return (True, "\n".join(lines), {"type": "profile"})

        if cmd.startswith("/profile"):
            profile_parts = arg.split(maxsplit=1)
            if not profile_parts:
                raise ValueError("Usage: /profile <create|switch|delete> <name>")
            action = profile_parts[0].lower()
            value = profile_parts[1].strip() if len(profile_parts) > 1 else ""
            if action == "create":
                name = self.create_profile(value)
                return (True, f"Profile created: {name}", {"type": "profile"})
            if action == "switch":
                name = self.switch_profile(value)
                return (True, f"Switched to profile: {name}", {"type": "profile"})
            if action == "delete":
                name = self.delete_profile(value)
                return (True, f"Deleted profile: {name}", {"type": "profile"})
            if action == "export":
                path = self.export_active_profile()
                return (True, f"Profile exported to: {path}", {"type": "profile"})
            raise ValueError("Usage: /profile <create|switch|delete> <name>")

        if cmd.startswith("/task"):
            task_parts = arg.split(maxsplit=1)
            if not task_parts:
                raise ValueError("Usage: /task <add|list|done|remove|clear> ...")
            action = task_parts[0].lower()
            value = task_parts[1].strip() if len(task_parts) > 1 else ""
            if action == "add":
                task = self.add_task(value)
                return (
                    True,
                    f"Task added [{task['id']}]: {task['text']}",
                    {"type": "task"},
                )
            if action == "list":
                tasks = self.list_tasks()
                if not tasks:
                    return (True, "No tasks yet.", {"type": "task"})
                lines = ["Tasks:"]
                for t in tasks:
                    status = "done" if t.get("done") else "todo"
                    priority = t.get("priority", "medium")
                    due = t.get("due_date", "") or "none"
                    lines.append(
                        f"  [{t.get('id')}] ({status}) [p:{priority}] [due:{due}] {t.get('text')}"
                    )
                return (True, "\n".join(lines), {"type": "task"})
            if action == "done":
                done_task = self.complete_task(int(value))
                return (
                    True,
                    f"Task completed [{done_task['id']}]: {done_task['text']}",
                    {"type": "task"},
                )
            if action == "edit":
                parts = [p.strip() for p in value.split("|")]
                if len(parts) < 2:
                    raise ValueError(
                        "Usage: /task edit <id>|<text>|<priority>|<YYYY-MM-DD>"
                    )
                task_id = int(parts[0])
                text = parts[1] if len(parts) > 1 and parts[1] else None
                priority = parts[2] if len(parts) > 2 and parts[2] else None
                due_date = parts[3] if len(parts) > 3 and parts[3] else None
                updated = self.edit_task(
                    task_id,
                    text=text,
                    priority=priority,
                    due_date=due_date,
                )
                return (
                    True,
                    f"Task updated [{updated['id']}]: {updated['text']}",
                    {"type": "task"},
                )
            if action == "postpone":
                subparts = value.split(maxsplit=1)
                if not subparts or not subparts[0]:
                    raise ValueError("Usage: /task postpone <id> [days]")
                task_id = int(subparts[0])
                days = int(subparts[1]) if len(subparts) > 1 else 1
                updated = self.postpone_task(task_id, days=days)
                return (
                    True,
                    f"Task postponed [{updated['id']}], new due: {updated.get('due_date') or 'none'}",
                    {"type": "task"},
                )
            if action == "remove":
                self.remove_task(int(value))
                return (True, f"Task removed: {value}", {"type": "task"})
            if action == "clear":
                self.clear_tasks()
                return (True, "All tasks cleared.", {"type": "task"})
            raise ValueError("Usage: /task <add|list|done|edit|postpone|remove|clear> ...")

        if cmd.startswith("/memory"):
            mem_parts = arg.split(maxsplit=1)
            if not mem_parts:
                raise ValueError("Usage: /memory <add|list|clear|recall> ...")
            action = mem_parts[0].lower()
            value = mem_parts[1].strip() if len(mem_parts) > 1 else ""
            if action == "add":
                note = self.add_memory_note(value)
                return (True, f"Memory saved: {note}", {"type": "memory"})
            if action == "list":
                notes = self.list_memory_notes()
                if not notes:
                    return (True, "No memory notes saved.", {"type": "memory"})
                lines = ["Memory notes:"]
                for idx, note in enumerate(notes, start=1):
                    lines.append(f"  {idx}. {note}")
                return (True, "\n".join(lines), {"type": "memory"})
            if action == "clear":
                self.clear_memory_notes()
                return (True, "Memory notes cleared.", {"type": "memory"})
            if action == "recall":
                notes = self.recall_memory_notes(value)
                if not notes:
                    return (True, "No relevant memory found.", {"type": "memory"})
                lines = ["Relevant memory:"]
                for note in notes:
                    lines.append(f"  - {note}")
                return (True, "\n".join(lines), {"type": "memory"})
            raise ValueError("Usage: /memory <add|list|clear|recall> ...")

        if cmd == "/prefs":
            p = self.get_preferences()
            msg = (
                "Current preferences:\n"
                f"  active_profile: {self.active_profile}\n"
                f"  name: {p.get('name', 'User')}\n"
                f"  mode: {p.get('mode', 'study')} ({MODES.get(p.get('mode', 'study'), 'Unknown')})\n"
                f"  short_responses: {p.get('short_responses', 'false')}\n"
                f"  learning_style: {p.get('learning_style', 'step-by-step')}\n"
                f"  focus_goal: {p.get('focus_goal', '')}\n"
                f"  interests: {p.get('interests', '')}\n"
                f"  tasks: {len(self.list_tasks())}\n"
                f"  memory_notes: {len(self.list_memory_notes())}"
            )
            return (True, msg, {"type": "prefs"})

        if cmd == "/reset":
            self.reset_chat()
            return (True, "Conversation context reset.", {"type": "session"})

        if cmd == "/export":
            path = self.export_chat(arg)
            return (True, f"Chat exported to: {path}", {"type": "export"})

        if cmd == "/exit":
            return (True, "Goodbye from Aiden - The Smart AI Companion.", {"type": "exit"})

        raise ValueError("Unknown command. Type /help for supported commands.")

    def chat(self, user_text: str) -> str:
        if self.is_unsafe_prompt(user_text):
            return (
                "I can't help with harmful or illegal requests. "
                "I can help with safe and responsible alternatives."
            )

        user_content = self._build_user_content(user_text)
        self.messages.append({"role": "user", "content": user_content})
        self._trim_messages()

        if self.client is None:
            assistant_text = self._chat_local_fallback(user_text)
            self.messages.append({"role": "assistant", "content": assistant_text})
            return assistant_text

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.4,
            )
            assistant_text = response.choices[0].message.content or ""
            self.model_healthy = True
            self.last_model_error = ""
        except Exception as exc:
            if not self.dev_mode:
                raise
            self.model_healthy = False
            self.last_model_error = (
                f"Model API request failed ({type(exc).__name__}): {exc}. "
                "Using local fallback mode."
            )
            assistant_text = self._chat_local_fallback(user_text)
        self.messages.append({"role": "assistant", "content": assistant_text})
        return assistant_text

    def chat_stream(self, user_text: str) -> Iterator[str]:
        if self.is_unsafe_prompt(user_text):
            safe_text = (
                "I can't help with harmful or illegal requests. "
                "I can help with safe and responsible alternatives."
            )
            self.messages.append({"role": "assistant", "content": safe_text})
            yield safe_text
            return

        user_content = self._build_user_content(user_text)
        self.messages.append({"role": "user", "content": user_content})
        self._trim_messages()

        if self.client is None:
            assistant_text = self._chat_local_fallback(user_text)
            self.messages.append({"role": "assistant", "content": assistant_text})
            for token in assistant_text.split(" "):
                yield token + " "
            return

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.4,
                stream=True,
            )

            parts: List[str] = []
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = delta.content or ""
                if not text:
                    continue
                parts.append(text)
                yield text

            assistant_text = "".join(parts)
            self.model_healthy = True
            self.last_model_error = ""
        except Exception as exc:
            if not self.dev_mode:
                raise
            self.model_healthy = False
            self.last_model_error = (
                f"Model API stream failed ({type(exc).__name__}): {exc}. "
                "Using local fallback mode."
            )
            assistant_text = self._chat_local_fallback(user_text)
            for token in assistant_text.split(" "):
                yield token + " "
        self.messages.append({"role": "assistant", "content": assistant_text})

    def _build_user_content(self, user_text: str) -> str:
        # Embed recalled memory into the user turn so it is tied to this specific
        # message and does not accumulate as a separate system entry.
        user_content = user_text
        recalled = self.recall_memory_notes(user_text, limit=2)
        if recalled:
            context_note = "[Memory context: " + " | ".join(recalled) + "]"
            user_content = f"{context_note}\n{user_text}"
        return user_content

    def _chat_local_fallback(self, user_text: str) -> str:
        mode = self.preferences.get("mode", "study")
        name = self.preferences.get("name", "User")

        cleaned = user_text.strip()
        lowered = cleaned.lower()
        words = [w for w in re.findall(r"[A-Za-z0-9']+", cleaned)]
        is_question = cleaned.endswith("?") or cleaned.lower().startswith(
            ("what", "why", "how", "when", "where", "who", "can", "should")
        )

        if lowered.startswith("summarize:") or lowered.startswith("summary:"):
            source = cleaned.split(":", 1)[1].strip()
            points = self._fallback_key_points(source or cleaned)
            return (
                "Local Dev Mode summary (no model API):\n"
                + "\n".join(f"- {point}" for point in points)
                + "\nSet OPENAI_API_KEY in .env to enable full AI responses."
            )

        if lowered.startswith("plan:") or "plan" in lowered:
            plan = self._fallback_build_plan(cleaned, mode)
            return (
                "Local Dev Mode action plan (no model API):\n"
                + "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan, start=1))
                + "\nSet OPENAI_API_KEY in .env to enable full AI responses."
            )

        if lowered.startswith("checklist:") or "checklist" in lowered:
            checklist = self._fallback_build_checklist(cleaned)
            return (
                "Local Dev Mode checklist (no model API):\n"
                + "\n".join(f"- [ ] {item}" for item in checklist)
                + "\nSet OPENAI_API_KEY in .env to enable full AI responses."
            )

        if mode == "coding":
            mode_line = "Local Dev Mode is active, so I cannot call the model API."
            help_line = (
                "I can still help with a practical debugging flow:\n"
                "1. Reproduce consistently\n"
                "2. Isolate the failing function\n"
                "3. Add logs/assertions around inputs and outputs\n"
                "4. Verify expected behavior with a small test"
            )
        elif mode == "idea":
            mode_line = "Local Dev Mode is active, so this response is generated without the model API."
            help_line = (
                "I can still brainstorm with structure:\n"
                "1. Define your goal\n"
                "2. List constraints\n"
                "3. Generate 3 options\n"
                "4. Pick one and map next actions"
            )
        elif mode == "productivity":
            mode_line = "Local Dev Mode is active, so this response is generated without the model API."
            help_line = (
                "I can still build a focused plan:\n"
                "1. Top priority task (45 min)\n"
                "2. Secondary task (30 min)\n"
                "3. Admin cleanup (15 min)\n"
                "4. Review and adjust"
            )
        else:
            mode_line = "Local Dev Mode is active, so this response is generated without the model API."
            help_line = (
                "I can still provide a study structure:\n"
                "1. Core concept\n"
                "2. Worked example\n"
                "3. Practice step\n"
                "4. Quick recap"
            )

        guidance = ""
        if len(words) > 50:
            guidance = (
                "\nQuick summary of your message:\n"
                f"- {self._fallback_summary(cleaned)}"
            )
        elif is_question:
            guidance = (
                "\nI detected a question. For a stronger answer in local mode, add context: "
                "goal, current attempt, and expected result."
            )

        recalled = self.recall_memory_notes(user_text, limit=2)
        recall_line = ""
        if recalled:
            recall_line = "\nRelevant memory: " + " | ".join(recalled)

        return (
            f"{mode_line}\n"
            f"Hi {name}, I received: \"{user_text}\".\n"
            f"{help_line}{guidance}{recall_line}\n"
            "Set OPENAI_API_KEY in .env to enable full AI responses."
        )

    @staticmethod
    def _fallback_summary(text: str) -> str:
        chunks = [p.strip() for p in re.split(r"[.!?]\s+", text) if p.strip()]
        if not chunks:
            return text[:180]
        lead = chunks[0]
        if len(lead) > 180:
            return lead[:177] + "..."
        return lead

    @staticmethod
    def _fallback_key_points(text: str) -> List[str]:
        chunks = [p.strip() for p in re.split(r"[.!?]\s+", text) if p.strip()]
        if not chunks:
            return ["No detailed text provided. Add more context after summarize:."]
        points = chunks[:3]
        if len(chunks) > 3:
            points.append("Additional details omitted for brevity in local mode.")
        return points

    @staticmethod
    def _fallback_extract_focus(text: str) -> str:
        tokens = re.findall(r"[A-Za-z0-9']+", text)
        if not tokens:
            return "your current goal"
        return " ".join(tokens[:8])

    def _fallback_build_plan(self, text: str, mode: str) -> List[str]:
        focus = self._fallback_extract_focus(text)
        if mode == "coding":
            return [
                f"Define expected behavior for {focus}",
                "Reproduce the issue with minimal input",
                "Add targeted logs and assertions",
                "Apply one focused fix and retest",
                "Document the root cause and prevention step",
            ]
        if mode == "productivity":
            return [
                f"Clarify success criteria for {focus}",
                "Break work into 30-45 minute blocks",
                "Do the highest impact task first",
                "Schedule a short review checkpoint",
                "Capture next actions before stopping",
            ]
        return [
            f"Define the objective for {focus}",
            "Collect constraints and assumptions",
            "Draft 2-3 implementation options",
            "Choose one option and run a small test",
            "Review results and iterate",
        ]

    @staticmethod
    def _fallback_build_checklist(text: str) -> List[str]:
        focus = AidenEngine._fallback_extract_focus(text)
        return [
            f"Confirm scope for {focus}",
            "List required inputs and dependencies",
            "Define completion criteria",
            "Execute first pass",
            "Verify output against criteria",
        ]
