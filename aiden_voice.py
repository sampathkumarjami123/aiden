from aiden_core import AidenEngine

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


def print_help() -> None:
    print("\nVoice Commands:")
    print("  /listen                   Capture one prompt from microphone")
    print("  /speak on|off             Toggle spoken responses")
    print("  /mode <study|coding|idea|productivity>")
    print("  /name <your_name>")
    print("  /short <on|off>")
    print("  /style <learning_style>")
    print("  /goal <focus_goal>")
    print("  /interests <comma separated interests>")
    print("  /prefs")
    print("  /reset")
    print("  /export [filename]")
    print("  /exit")


def listen_once(recognizer, microphone) -> str:
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)
    return recognizer.recognize_google(audio)


def main() -> None:
    engine = AidenEngine()

    tts_enabled = False
    tts = None
    if pyttsx3 is not None:
        tts = pyttsx3.init()
        tts.setProperty("rate", 180)

    recognizer = sr.Recognizer() if sr is not None else None
    microphone = sr.Microphone() if sr is not None else None

    print("Aiden Voice Mode")
    print("Type /help for commands. Type /listen to speak through your mic.\n")

    while True:
        user_text = input("You: ").strip()
        if not user_text:
            continue

        if user_text == "/help":
            print_help()
            continue

        if user_text == "/exit":
            print("Goodbye from Aiden - The Smart AI Companion.")
            break

        if user_text.startswith("/speak "):
            value = user_text.split(maxsplit=1)[1].strip().lower()
            if value not in {"on", "off"}:
                print("System: Usage: /speak <on|off>")
                continue
            if value == "on" and tts is None:
                print("System: pyttsx3 not installed. Run: pip install pyttsx3")
                continue
            tts_enabled = value == "on"
            print(f"System: Spoken responses {'enabled' if tts_enabled else 'disabled'}.")
            continue

        if user_text == "/listen":
            if recognizer is None or microphone is None:
                print(
                    "System: speech_recognition not installed. Run: pip install SpeechRecognition"
                )
                continue
            try:
                heard = listen_once(recognizer, microphone)
                print(f"You (voice): {heard}")
                user_text = heard
            except Exception as exc:
                print(f"System: Could not capture voice input: {exc}")
                continue

        try:
            handled, output, meta = engine.handle_command(user_text)
            if handled:
                print(f"System: {output}")
                if meta.get("type") == "exit":
                    break
                continue
        except ValueError as exc:
            print(f"System: {exc}")
            continue

        try:
            response = engine.chat(user_text)
            print(f"Aiden: {response}\n")
            if tts_enabled and tts is not None:
                tts.say(response)
                tts.runAndWait()
        except Exception as exc:
            print(f"System: Request failed: {exc}")


if __name__ == "__main__":
    main()
