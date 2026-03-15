import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk

from aiden_core import AidenEngine, MODES

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class AidenDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Aiden - Smart AI Companion")
        self.root.geometry("920x680")
        self.root.configure(bg="#f4efe6")

        self.engine = AidenEngine()
        self.last_response = ""

        self.tts = None
        if pyttsx3 is not None:
            self.tts = pyttsx3.init()
            self.tts.setProperty("rate", 185)

        self._build_ui()
        self._load_preferences_into_ui()
        self._append_message("Aiden", "Hello. I am Aiden - The Smart AI Companion. How can I help?")

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, bg="#f4efe6", pady=10)
        top.pack(fill="x")

        title = tk.Label(
            top,
            text="Aiden",
            font=("Georgia", 24, "bold"),
            bg="#f4efe6",
            fg="#1f3a5f",
        )
        title.pack(side="left", padx=16)

        subtitle = tk.Label(
            top,
            text="The Smart AI Companion",
            font=("Trebuchet MS", 11),
            bg="#f4efe6",
            fg="#4f6d8a",
        )
        subtitle.pack(side="left", padx=8)

        controls = tk.Frame(self.root, bg="#f4efe6")
        controls.pack(fill="x", padx=16, pady=6)

        tk.Label(controls, text="Mode", bg="#f4efe6").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar()
        self.mode_combo = ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=list(MODES.keys()),
            state="readonly",
            width=14,
        )
        self.mode_combo.grid(row=1, column=0, padx=(0, 12), pady=(2, 6), sticky="w")
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_changed)

        tk.Label(controls, text="Name", bg="#f4efe6").grid(row=0, column=1, sticky="w")
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(controls, textvariable=self.name_var, width=20)
        self.name_entry.grid(row=1, column=1, padx=(0, 12), pady=(2, 6), sticky="w")

        tk.Label(controls, text="Learning Style", bg="#f4efe6").grid(row=0, column=2, sticky="w")
        self.style_var = tk.StringVar()
        self.style_entry = tk.Entry(controls, textvariable=self.style_var, width=24)
        self.style_entry.grid(row=1, column=2, padx=(0, 12), pady=(2, 6), sticky="w")

        self.short_var = tk.BooleanVar(value=False)
        self.short_check = tk.Checkbutton(
            controls,
            text="Concise responses",
            variable=self.short_var,
            bg="#f4efe6",
            command=self._on_short_changed,
        )
        self.short_check.grid(row=1, column=3, padx=(0, 12), sticky="w")

        save_button = tk.Button(
            controls,
            text="Save Profile",
            command=self._save_profile,
            bg="#1f3a5f",
            fg="white",
            relief="flat",
            padx=12,
        )
        save_button.grid(row=1, column=4, sticky="w")

        tk.Label(controls, text="Focus Goal", bg="#f4efe6").grid(row=2, column=0, sticky="w")
        self.goal_var = tk.StringVar()
        self.goal_entry = tk.Entry(controls, textvariable=self.goal_var, width=38)
        self.goal_entry.grid(row=3, column=0, columnspan=2, padx=(0, 12), pady=(2, 0), sticky="w")

        tk.Label(controls, text="Interests", bg="#f4efe6").grid(row=2, column=2, sticky="w")
        self.interests_var = tk.StringVar()
        self.interests_entry = tk.Entry(controls, textvariable=self.interests_var, width=38)
        self.interests_entry.grid(row=3, column=2, columnspan=2, padx=(0, 12), pady=(2, 0), sticky="w")

        reset_btn = tk.Button(
            controls,
            text="Reset Chat",
            command=self._reset_chat,
            bg="#8f4e4e",
            fg="white",
            relief="flat",
            padx=10,
        )
        reset_btn.grid(row=3, column=4, sticky="w", pady=(2, 0))

        export_btn = tk.Button(
            controls,
            text="Export Chat",
            command=self._export_chat,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        export_btn.grid(row=2, column=4, sticky="w")

        advanced = tk.Frame(self.root, bg="#f4efe6")
        advanced.pack(fill="x", padx=16, pady=(0, 8))

        profile_box = tk.LabelFrame(advanced, text="Profiles", bg="#f4efe6")
        profile_box.pack(side="left", fill="both", padx=(0, 10))

        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            profile_box,
            textvariable=self.profile_var,
            state="readonly",
            width=20,
        )
        self.profile_combo.grid(row=0, column=0, padx=8, pady=8)

        switch_profile_btn = tk.Button(
            profile_box,
            text="Switch",
            command=self._switch_profile,
            bg="#1f3a5f",
            fg="white",
            relief="flat",
            padx=10,
        )
        switch_profile_btn.grid(row=0, column=1, padx=4, pady=8)

        create_profile_btn = tk.Button(
            profile_box,
            text="Create",
            command=self._create_profile,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        create_profile_btn.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")

        delete_profile_btn = tk.Button(
            profile_box,
            text="Delete",
            command=self._delete_profile,
            bg="#8f4e4e",
            fg="white",
            relief="flat",
            padx=10,
        )
        delete_profile_btn.grid(row=1, column=1, padx=4, pady=(0, 8), sticky="w")

        tasks_box = tk.LabelFrame(advanced, text="Tasks", bg="#f4efe6")
        tasks_box.pack(side="left", fill="x", expand=True)

        self.task_input_var = tk.StringVar()
        task_entry = tk.Entry(tasks_box, textvariable=self.task_input_var)
        task_entry.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        task_entry.bind("<Return>", lambda _event: self._add_task())
        tasks_box.grid_columnconfigure(0, weight=1)

        add_task_btn = tk.Button(
            tasks_box,
            text="Add",
            command=self._add_task,
            bg="#ef7f45",
            fg="white",
            relief="flat",
            padx=10,
        )
        add_task_btn.grid(row=0, column=1, padx=4, pady=8)

        tk.Label(tasks_box, text="Due", bg="#f4efe6").grid(row=1, column=0, padx=8, sticky="w")
        self.task_due_var = tk.StringVar()
        task_due_entry = tk.Entry(tasks_box, textvariable=self.task_due_var)
        task_due_entry.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")

        tk.Label(tasks_box, text="Priority", bg="#f4efe6").grid(row=1, column=1, padx=4, sticky="w")
        self.task_priority_var = tk.StringVar(value="medium")
        task_priority_combo = ttk.Combobox(
            tasks_box,
            textvariable=self.task_priority_var,
            values=["high", "medium", "low"],
            state="readonly",
            width=10,
        )
        task_priority_combo.grid(row=2, column=1, padx=4, pady=(0, 6), sticky="w")

        self.tasks_listbox = tk.Listbox(tasks_box, height=4)
        self.tasks_listbox.grid(row=3, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        tk.Label(tasks_box, text="Show", bg="#f4efe6").grid(row=4, column=0, padx=8, sticky="w")
        self.task_filter_var = tk.StringVar(value="all")
        task_filter_combo = ttk.Combobox(
            tasks_box,
            textvariable=self.task_filter_var,
            values=["all", "pending", "done"],
            state="readonly",
            width=10,
        )
        task_filter_combo.grid(row=4, column=1, padx=4, pady=(0, 8), sticky="e")
        task_filter_combo.bind("<<ComboboxSelected>>", lambda _event: self._render_tasks())

        done_task_btn = tk.Button(
            tasks_box,
            text="Done",
            command=self._mark_task_done,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        done_task_btn.grid(row=5, column=0, padx=8, pady=(0, 8), sticky="w")

        remove_task_btn = tk.Button(
            tasks_box,
            text="Remove",
            command=self._remove_task,
            bg="#8f4e4e",
            fg="white",
            relief="flat",
            padx=10,
        )
        remove_task_btn.grid(row=5, column=0, padx=8, pady=(0, 8))

        clear_task_btn = tk.Button(
            tasks_box,
            text="Clear",
            command=self._clear_tasks,
            bg="#8f4e4e",
            fg="white",
            relief="flat",
            padx=10,
        )
        clear_task_btn.grid(row=5, column=1, padx=4, pady=(0, 8), sticky="e")

        edit_task_btn = tk.Button(
            tasks_box,
            text="Edit",
            command=self._edit_task,
            bg="#1f3a5f",
            fg="white",
            relief="flat",
            padx=10,
        )
        edit_task_btn.grid(row=6, column=0, padx=8, pady=(0, 8), sticky="w")

        postpone_task_btn = tk.Button(
            tasks_box,
            text="+1 Day",
            command=self._postpone_task,
            bg="#1f3a5f",
            fg="white",
            relief="flat",
            padx=10,
        )
        postpone_task_btn.grid(row=6, column=1, padx=4, pady=(0, 8), sticky="e")

        memory_box = tk.LabelFrame(advanced, text="Memory Notes", bg="#f4efe6")
        memory_box.pack(side="left", fill="both", padx=(10, 0))

        self.memory_input_var = tk.StringVar()
        memory_entry = tk.Entry(memory_box, textvariable=self.memory_input_var, width=32)
        memory_entry.grid(row=0, column=0, padx=8, pady=8)
        memory_entry.bind("<Return>", lambda _event: self._add_memory_note())

        add_memory_btn = tk.Button(
            memory_box,
            text="Save",
            command=self._add_memory_note,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        add_memory_btn.grid(row=0, column=1, padx=4, pady=8)

        self.memory_listbox = tk.Listbox(memory_box, height=6, width=48)
        self.memory_listbox.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8))

        clear_memory_btn = tk.Button(
            memory_box,
            text="Clear",
            command=self._clear_memory_notes,
            bg="#8f4e4e",
            fg="white",
            relief="flat",
            padx=10,
        )
        clear_memory_btn.grid(row=2, column=1, padx=4, pady=(0, 8), sticky="e")

        self.memory_search_var = tk.StringVar()
        memory_search_entry = tk.Entry(memory_box, textvariable=self.memory_search_var, width=32)
        memory_search_entry.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")
        memory_search_entry.bind("<Return>", lambda _event: self._search_memory_notes())

        search_memory_btn = tk.Button(
            memory_box,
            text="Search",
            command=self._search_memory_notes,
            bg="#1f3a5f",
            fg="white",
            relief="flat",
            padx=10,
        )
        search_memory_btn.grid(row=2, column=1, padx=4, pady=(0, 8), sticky="w")

        export_profile_btn = tk.Button(
            memory_box,
            text="Export Profile",
            command=self._export_active_profile,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        export_profile_btn.grid(row=3, column=0, padx=8, pady=(0, 8), sticky="w")

        import_profile_btn = tk.Button(
            memory_box,
            text="Import Profile",
            command=self._import_profile_json,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=10,
        )
        import_profile_btn.grid(row=3, column=1, padx=4, pady=(0, 8), sticky="e")

        chat_container = tk.Frame(self.root, bg="#f4efe6")
        chat_container.pack(fill="both", expand=True, padx=16, pady=8)

        self.chat_box = scrolledtext.ScrolledText(
            chat_container,
            wrap="word",
            font=("Consolas", 11),
            bg="#fffdfa",
            fg="#1a1a1a",
            insertbackground="#1a1a1a",
        )
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.configure(state="disabled")

        bottom = tk.Frame(self.root, bg="#f4efe6", pady=10)
        bottom.pack(fill="x", padx=16)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(bottom, textvariable=self.input_var, font=("Segoe UI", 11))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda _event: self.send_message())

        send_btn = tk.Button(
            bottom,
            text="Send",
            command=self.send_message,
            bg="#ef7f45",
            fg="white",
            relief="flat",
            padx=16,
        )
        send_btn.pack(side="left", padx=(0, 8))

        speak_btn = tk.Button(
            bottom,
            text="Speak Last",
            command=self.speak_last_response,
            bg="#3b6d65",
            fg="white",
            relief="flat",
            padx=14,
        )
        speak_btn.pack(side="left")

    def _load_preferences_into_ui(self) -> None:
        prefs = self.engine.get_preferences()
        self.mode_var.set(prefs.get("mode", "study"))
        self.name_var.set(prefs.get("name", "User"))
        self.short_var.set(prefs.get("short_responses", "false") == "true")
        self.style_var.set(prefs.get("learning_style", "step-by-step"))
        self.goal_var.set(prefs.get("focus_goal", ""))
        self.interests_var.set(prefs.get("interests", ""))
        self._refresh_profile_list()
        self._render_tasks()
        self._render_memory_notes()

    def _refresh_profile_list(self) -> None:
        profiles = self.engine.list_profiles()
        self.profile_combo["values"] = profiles
        active = self.engine.get_preferences().get("active_profile", "default")
        self.profile_var.set(active)

    def _switch_profile(self) -> None:
        target = self.profile_var.get().strip()
        if not target:
            return
        try:
            switched = self.engine.switch_profile(target)
            self._append_message("System", f"Switched to profile: {switched}")
            self._load_preferences_into_ui()
        except ValueError as exc:
            messagebox.showerror("Profile Error", str(exc))

    def _create_profile(self) -> None:
        name = simpledialog.askstring("Create Profile", "Profile name:")
        if not name:
            return
        try:
            created = self.engine.create_profile(name)
            self._append_message("System", f"Profile created: {created}")
            self._refresh_profile_list()
        except ValueError as exc:
            messagebox.showerror("Profile Error", str(exc))

    def _delete_profile(self) -> None:
        target = self.profile_var.get().strip()
        if not target:
            return
        try:
            deleted = self.engine.delete_profile(target)
            self._append_message("System", f"Deleted profile: {deleted}")
            self._load_preferences_into_ui()
        except ValueError as exc:
            messagebox.showerror("Profile Error", str(exc))

    def _render_tasks(self) -> None:
        self.tasks_listbox.delete(0, "end")
        tasks = self.engine.list_tasks()

        filter_mode = (self.task_filter_var.get().strip().lower() or "all")
        if filter_mode == "pending":
            tasks = [task for task in tasks if not task.get("done")]
        elif filter_mode == "done":
            tasks = [task for task in tasks if task.get("done")]

        if not tasks:
            self.tasks_listbox.insert("end", "(no tasks)")
            return
        for task in tasks:
            status = "done" if task.get("done") else "todo"
            priority = task.get("priority", "medium")
            due = task.get("due_date", "") or "none"
            self.tasks_listbox.insert(
                "end",
                f"[{task.get('id')}] ({status}) [p:{priority}] [due:{due}] {task.get('text')}",
            )

    def _render_memory_notes(self) -> None:
        self.memory_listbox.delete(0, "end")
        notes = self.engine.list_memory_notes()
        if not notes:
            self.memory_listbox.insert("end", "(no memory notes)")
            return
        for note in notes:
            self.memory_listbox.insert("end", note)

    def _selected_task_id(self) -> int | None:
        selected = self.tasks_listbox.curselection()
        if not selected:
            return None
        value = self.tasks_listbox.get(selected[0])
        if not value.startswith("["):
            return None
        try:
            task_id_str = value.split("]", maxsplit=1)[0].replace("[", "")
            return int(task_id_str)
        except ValueError:
            return None

    def _add_task(self) -> None:
        text = self.task_input_var.get().strip()
        if not text:
            return
        try:
            task = self.engine.add_task(
                text,
                due_date=self.task_due_var.get().strip(),
                priority=self.task_priority_var.get().strip().lower(),
            )
            self.task_input_var.set("")
            self.task_due_var.set("")
            self.task_priority_var.set("medium")
            self._append_message("System", f"Task added [{task['id']}]: {task['text']}")
            self._render_tasks()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def _mark_task_done(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            done = self.engine.complete_task(task_id)
            self._append_message("System", f"Task completed [{done['id']}]: {done['text']}")
            self._render_tasks()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def _edit_task(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            updated = self.engine.edit_task(
                task_id,
                text=self.task_input_var.get().strip() or None,
                due_date=self.task_due_var.get().strip(),
                priority=self.task_priority_var.get().strip().lower() or None,
            )
            self._append_message("System", f"Task updated [{updated['id']}]: {updated['text']}")
            self._render_tasks()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def _postpone_task(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            updated = self.engine.postpone_task(task_id, days=1)
            self._append_message(
                "System",
                f"Task postponed [{updated['id']}], new due: {updated.get('due_date') or 'none'}",
            )
            self._render_tasks()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def _remove_task(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            self.engine.remove_task(task_id)
            self._append_message("System", f"Task removed: {task_id}")
            self._render_tasks()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def _clear_tasks(self) -> None:
        self.engine.clear_tasks()
        self._append_message("System", "All tasks cleared.")
        self._render_tasks()

    def _add_memory_note(self) -> None:
        note = self.memory_input_var.get().strip()
        if not note:
            return
        try:
            saved = self.engine.add_memory_note(note)
            self.memory_input_var.set("")
            self._append_message("System", f"Memory saved: {saved}")
            self._render_memory_notes()
        except ValueError as exc:
            messagebox.showerror("Memory Error", str(exc))

    def _clear_memory_notes(self) -> None:
        self.engine.clear_memory_notes()
        self._append_message("System", "Memory notes cleared.")
        self._render_memory_notes()

    def _search_memory_notes(self) -> None:
        query = self.memory_search_var.get().strip()
        if not query:
            self._render_memory_notes()
            return
        notes = self.engine.recall_memory_notes(query, limit=20)
        self.memory_listbox.delete(0, "end")
        if not notes:
            self.memory_listbox.insert("end", "(no matches)")
            return
        for note in notes:
            self.memory_listbox.insert("end", note)

    def _export_active_profile(self) -> None:
        path = self.engine.export_active_profile()
        self._append_message("System", f"Profile exported to: {path}")

    def _import_profile_json(self) -> None:
        raw = simpledialog.askstring(
            "Import Profile JSON",
            "Paste profile JSON payload with profile_name and profile keys:",
        )
        if not raw:
            return
        try:
            payload = json.loads(raw)
            imported = self.engine.import_profile_from_json(
                str(payload.get("profile_name", "")),
                payload.get("profile", {}),
            )
            self._append_message("System", f"Imported profile: {imported}")
            self._load_preferences_into_ui()
        except (json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("Import Error", str(exc))

    def _append_message(self, speaker: str, text: str) -> None:
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{speaker}: {text}\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _on_mode_changed(self, _event=None) -> None:
        mode = self.mode_var.get().strip().lower()
        try:
            mode_name = self.engine.set_mode(mode)
            self._append_message("System", f"Mode switched to {mode_name}.")
        except ValueError as exc:
            messagebox.showerror("Invalid Mode", str(exc))

    def _save_profile(self) -> None:
        try:
            name = self.engine.set_name(self.name_var.get())
            style = self.engine.set_learning_style(self.style_var.get())
            goal = self.engine.set_focus_goal(self.goal_var.get())
            interests = self.engine.set_interests(self.interests_var.get())
            self._append_message(
                "System",
                (
                    f"Profile saved. name={name}, style={style}, "
                    f"goal={goal or '(cleared)'}, interests={interests or '(cleared)'}"
                ),
            )
        except ValueError as exc:
            messagebox.showerror("Invalid Profile", str(exc))

    def _on_short_changed(self) -> None:
        self.engine.set_short_responses(self.short_var.get())
        state = "enabled" if self.short_var.get() else "disabled"
        self._append_message("System", f"Concise response preference {state}.")

    def _reset_chat(self) -> None:
        self.engine.reset_chat()
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self._append_message("System", "Conversation context reset.")

    def _export_chat(self) -> None:
        path = self.engine.export_chat()
        self._append_message("System", f"Chat exported to: {path}")

    def send_message(self) -> None:
        user_text = self.input_var.get().strip()
        if not user_text:
            return

        self.input_var.set("")
        self._append_message("You", user_text)

        worker = threading.Thread(target=self._fetch_response, args=(user_text,), daemon=True)
        worker.start()

    def _fetch_response(self, user_text: str) -> None:
        try:
            handled, command_output, meta = self.engine.handle_command(user_text)
            if handled:
                self.root.after(0, lambda: self._append_message("System", command_output))
                self.root.after(0, self._load_preferences_into_ui)
                if meta.get("type") == "session":
                    self.root.after(
                        0,
                        lambda: self._append_message(
                            "Aiden",
                            "Context reset complete. What would you like to do next?",
                        ),
                    )
                if meta.get("type") == "exit":
                    self.root.after(0, self.root.destroy)
                return

            response = self.engine.chat(user_text)
            self.last_response = response
            self.root.after(0, lambda: self._append_message("Aiden", response))
        except Exception as exc:
            self.root.after(
                0,
                lambda: self._append_message(
                    "System", f"Request failed: {exc}"
                ),
            )

    def speak_last_response(self) -> None:
        if not self.last_response:
            messagebox.showinfo("No Response", "There is no response to speak yet.")
            return

        if self.tts is None:
            messagebox.showinfo(
                "TTS Not Installed",
                "Install pyttsx3 to enable speech output: pip install pyttsx3",
            )
            return

        self.tts.say(self.last_response)
        self.tts.runAndWait()


def main() -> None:
    root = tk.Tk()
    app = AidenDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
