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

## 🌟 Latest Features (v1.0)

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

## Quick Start Scripts (Windows PowerShell)

Use these helper scripts after setup:

```powershell
.\scripts\setup.ps1
.\scripts\start.ps1 -Mode web -Reload
.\scripts\start.ps1 -Mode cli
.\scripts\start.ps1 -Mode desktop
.\scripts\start.ps1 -Mode voice
.\scripts\health-check.ps1
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
- `scripts/start.ps1`: one-command launcher for web, cli, desktop, and voice modes
- `scripts/health-check.ps1`: compile and web endpoint smoke test
- `preferences.json`: created automatically after first preference change
- `profiles.json`: active profile, profile settings, tasks, and memory notes
- `chat_exports/`: generated chat exports (`.md`)
- `web/templates/index.html`: web UI template
- `web/static/style.css`: web styling
- `web/static/app.js`: browser logic

## Notes

- `SpeechRecognition` may require additional microphone dependencies on some systems.
- If `pyttsx3` is unavailable, voice output is skipped safely.
- If `OPENAI_API_KEY` is not set and `AIDEN_DEV_MODE=true`, Aiden still runs with local fallback responses for UI testing.
- In local fallback mode, you can use prefixes for structured output:
	- `summarize: <text>`
	- `plan: <goal or task>`
	- `checklist: <goal or task>`
