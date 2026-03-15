# Aiden - The Smart AI Companion

> **🎉 PRODUCTION READY: 26 Features | Local-First | Fully Configured**

Aiden is a local AI assistant with:
- Friendly, teacher-like personality
- Study, Coding, Idea, and Productivity modes
- Conversation safety checks
- Context memory in current session
- Simple user preference memory across runs
- Multiple interfaces: CLI, Desktop UI, Web UI, and Voice Mode
- Advanced profile memory (learning style, focus goal, interests)
- Chat reset and chat export features
- Automatic context trimming for long sessions
- Multi-profile support (separate settings, tasks, and memory per profile)
- Built-in task manager commands
- User memory notes with relevance recall
- Visual profile and task controls in Web and Desktop UI
- Planner-style task metadata (priority and due date)
- Visual memory notes panel in Web and Desktop UI
- **NEW: 26 UI/UX Features** (Theme Selector, Bookmarks, Tagging, Dashboard, etc.)

---

## 🚀 Quick Links

| Task | Link |
|------|------|
| **Run Locally** | See Section 1) Setup below |
| **CLI Mode** | See Section 2) Run CLI |
| **Web UI** | See Section 4) Run Web UI |
| **Voice Mode** | See Section 5) Run Voice Mode |

---

## 🌟 Latest Features (v1.0.1)

### UI/UX Enhancements (26 Total)
- ✨ **5 Theme Presets** - Light, Dark, Nord, Dracula, Solarized
- 🏷️ **Conversation Tagging** - Organize with #hashtags
- 📌 **Message Bookmarks** - Save important messages
- 📊 **Statistics Dashboard** - Chat analytics and metrics
- ⚙️ **Advanced Settings** - Font size, notifications, modes
- ⌨️ **Keyboard Shortcuts** - Fast navigation
- 👍 **Message Reactions** - React to responses
- 💾 **Message Pinning** - Pin important messages
- 📤 **Conversation Export** - Save chats as JSON
- 🤖 **Quick Reply Suggestions** - Context-aware suggestions
- ...and 16 more features!

---

## 1) Setup

1. Open a terminal in this folder.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Set your OpenAI API key.

### Windows PowerShell example

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Or run one command:

```powershell
.\scripts\setup.ps1
```

Then edit `.env` and set:
- `OPENAI_API_KEY`
- Optional: `AIDEN_MODEL` (default is `gpt-5.3-codex`)
- Optional: `AIDEN_MAX_MESSAGES` (default is `30`)
- Optional: `AIDEN_DEV_MODE` (default is `true`; allows local fallback replies when key is missing)
- Optional: `AIDEN_DATA_DIR` (default is project root; stores profiles, exports, and logs)
- Optional: `AIDEN_RATE_LIMIT_WINDOW_SECONDS` (default is `60`)
- Optional: `AIDEN_RATE_LIMIT_PER_WINDOW` (default is `60`)
- Optional: `AIDEN_MAX_REQUEST_BYTES` (default is `65536`)
- Optional: `AIDEN_STREAM_MAX_SECONDS` (default is `120`; max stream duration guard)
- Optional: `AIDEN_LOG_LEVEL` (default is `INFO`)
- Optional: `AIDEN_LOG_MAX_BYTES` (default is `1048576`)
- Optional: `AIDEN_LOG_BACKUP_COUNT` (default is `3`)

## Quick Start Scripts (Windows PowerShell)

Use these helper scripts after setup:

```powershell
.\scripts\setup.ps1
.\scripts\start.ps1 -Mode web -Reload
.\scripts\start.ps1 -Mode web -Reload -OpenBrowser
.\scripts\start.ps1 -Mode web -Reload -Background -OpenBrowser
.\scripts\stop-web.ps1
.\scripts\status-web.ps1
.\scripts\web.ps1 -Action start -Reload -Background -OpenBrowser
.\scripts\web.ps1 -Action status
.\scripts\web.ps1 -Action doctor
.\scripts\web.ps1 -Action stop
.\scripts\start.ps1 -Mode cli
.\scripts\start.ps1 -Mode desktop
.\scripts\start.ps1 -Mode voice
.\scripts\start.ps1 -Mode doctor
.\scripts\start.ps1 -Mode doctor -OpenBrowser
.\scripts\test.ps1
.\scripts\quality-gate.ps1
.\scripts\health-check.ps1
.\scripts\health-check.ps1 -StartupTimeoutSeconds 60
.\scripts\runtime-check.ps1
.\scripts\logs.ps1 -Tail 100
.\scripts\logs.ps1 -Tail 100 -Follow
.\scripts\release.ps1 -Version v1.0.1 -DryRun
```

CI quality checks run automatically on pushes and pull requests via GitHub Actions.

## 2) Run CLI

```powershell
python aiden.py
```

## 3) Run Desktop UI (Tkinter)

```powershell
python aiden_desktop.py
```

Desktop includes:
- Profile switch/create/delete panel
- Task add/complete/remove/clear panel
- Task filter view (`all`, `pending`, `done`)
- Command-aware chat box (slash commands also work)

## 4) Run Web UI (FastAPI)

```powershell
uvicorn aiden_web:app --reload
```

Then open: `http://127.0.0.1:8000`

Web includes:
- Live profile manager (switch/create/delete)
- Interactive task board with done/remove actions
- Task priority and due date inputs
- Memory notes save and clear panel
- State sync with backend profile and task data
- Streaming assistant replies over `/api/chat/stream` (NDJSON chunks)
- Stop button to cancel in-progress streamed replies
- Automatic one-time retry on transient stream interruptions
- Runtime Details panel with one-click **Retest Model** diagnostics

## 5) Run Voice Mode

```powershell
python aiden_voice.py
```

In voice mode:
- Use `/listen` to capture microphone input.
- Use `/speak on` to enable spoken responses.

## 6) CLI Commands

- `/help`
- `/mode study`
- `/mode coding`
- `/mode idea`
- `/mode productivity`
- `/name Sam`
- `/short on`
- `/short off`
- `/style visual examples`
- `/goal finish Python basics in 2 weeks`
- `/interests AI, robotics, web development`
- `/profiles`
- `/profile create exam-prep`
- `/profile switch exam-prep`
- `/profile delete exam-prep`
- `/task add Revise calculus chapter 3`
- `/task list`
- `/task done 1`
- `/task remove 1`
- `/task clear`
- `/memory add Prefers visual explanations first`
- `/memory list`
- `/memory recall visual explanation`
- `/memory clear`
- `/prefs`
- `/reset`
- `/export`
- `/exit`

## Files

- `aiden_core.py`: shared engine for all interfaces
- `aiden.py`: CLI app
- `aiden_desktop.py`: desktop app
- `aiden_web.py`: web server app
- `aiden_voice.py`: voice-first app
- `aiden_prompt.md`: system instruction and personality
- `scripts/setup.ps1`: creates virtual environment, installs dependencies, and bootstraps `.env`
- `scripts/start.ps1`: one-command launcher for web, cli, desktop, voice, and doctor diagnostics mode
- `scripts/stop-web.ps1`: stops a background web server started by `start.ps1 -Mode web -Background`
- `scripts/status-web.ps1`: reports background web PID/process status plus `/health` reachability
- `scripts/web.ps1`: single entrypoint for web start/stop/status/doctor actions
- `scripts/test.ps1`: runs unit tests from the `tests/` folder
- `scripts/quality-gate.ps1`: runs tests plus health checks as one local gate
- `scripts/health-check.ps1`: compile and web endpoint smoke test
- `scripts/runtime-check.ps1`: live vs fallback runtime diagnosis and model retest helper
- `scripts/logs.ps1`: view or follow rotating API request logs
- `scripts/release.ps1`: validates release preconditions and creates semantic tags
- `preferences.json`: created automatically after first preference change
- `profiles.json`: active profile, profile settings, tasks, and memory notes
- `chat_exports/`: generated chat exports (`.md`)
- `logs/`: rotating API request logs (or under `AIDEN_DATA_DIR` when configured)
- `web/templates/index.html`: web UI template
- `web/static/style.css`: web styling
- `web/static/app.js`: browser logic

## Notes

- `SpeechRecognition` may require additional microphone dependencies on some systems.
- If `pyttsx3` is unavailable, voice output is skipped safely.
- If `OPENAI_API_KEY` is not set and `AIDEN_DEV_MODE=true`, Aiden still runs with local fallback responses for UI testing.
- Health endpoint for checks and monitoring: `GET /health`
- Streaming chat endpoint: `POST /api/chat/stream` (returns `application/x-ndjson` with `chunk` and `final` events)
- Stream failures emit a structured `error` event before the final metadata event
- Stream duration is bounded by `AIDEN_STREAM_MAX_SECONDS` to avoid runaway responses
- API responses include `x-request-id` for easier request tracing in logs.
- Runtime model retest endpoint: `POST /api/runtime/retest`
- In local fallback mode, you can use prefixes for structured output:
	- `summarize: <text>`
	- `plan: <goal or task>`
	- `checklist: <goal or task>`

## Live Model Troubleshooting

If the UI shows `Local Dev Mode` or `Fallback Mode` instead of `Live Model`:

1. Open **Runtime Details** in the web app.
2. Click **Retest Model**.
3. Check `last error` text for the root cause.

Common causes:

- `invalid_api_key` or `AuthenticationError`:
	- Generate a new key.
	- Update `OPENAI_API_KEY` in `.env`.
	- Restart the app.
- `insufficient_quota` or `RateLimitError`:
	- Enable billing or add credit in OpenAI for the project.
	- Wait 1-2 minutes.
	- Click **Retest Model** again.

Quick terminal check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/state | ConvertTo-Json -Depth 5
```

Expected live state:
- `runtime.mode_label = "live"`
- `runtime.has_model = true`
