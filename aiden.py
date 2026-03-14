from aiden_core import AidenEngine, MODES


def main() -> None:
    engine = AidenEngine()
    preferences = engine.get_preferences()

    print("Aiden - The Smart AI Companion")
    print(f"Active mode: {MODES.get(preferences.get('mode', 'study'), 'Study Mode')}")
    print("Type /help for commands. Type /exit to quit.\n")

    while True:
        user_text = input("You: ").strip()
        if not user_text:
            continue

        try:
            handled, command_output, meta = engine.handle_command(user_text)
            if handled:
                print(f"Aiden: {command_output}\n")
                if meta.get("type") == "exit":
                    raise SystemExit(0)
                continue
        except ValueError as exc:
            print(f"Aiden: {exc}\n")
            continue

        try:
            assistant_text = engine.chat(user_text)
            print(f"Aiden: {assistant_text}\n")
        except Exception as exc:
            print(f"Aiden: Request failed: {exc}\n")


if __name__ == "__main__":
    main()
