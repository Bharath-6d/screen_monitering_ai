import base64
import os
import threading
from io import BytesIO
from groq import Groq
from config import ANSWER_STYLE, GROQ_API_KEY

# ── Groq client (single instance, reused for all calls) ───────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)

_conversation_history = []
MAX_HISTORY = 10

PROFILE_FILE = "user_profile.txt"


# ── User memory ────────────────────────────────────────────────────────────────
def get_user_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return f.read().strip()
    return ""


def append_to_profile(fact):
    with open(PROFILE_FILE, "a") as f:
        f.write(f"- {fact}\n")
    print(f"[Memory] Learned: {fact}")


def _background_learn(user_text):
    """Silently checks if the user stated a permanent fact worth remembering."""
    try:
        from config import GROQ_TEXT_MODEL
        prompt = f"""Did the user state a permanent preference, rule, or personal fact in this message?
User message: "{user_text}"

If yes, reply ONLY with a concise summary (e.g. "User's name is John", "User prefers concise answers").
If no, reply EXACTLY with "NONE". Do not explain."""

        response = groq_client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        fact = response.choices[0].message.content.strip()
        if fact and "NONE" not in fact.upper():
            append_to_profile(fact)
    except Exception as e:
        print(f"[Memory Error] {e}")


# ── System prompt ──────────────────────────────────────────────────────────────
def get_system_prompt():
    prompt = """You are Jerry — a sharp, personal AI assistant. You talk like a real person, not a chatbot.

STRICT RULES — never break these:
- NO filler openers: "Certainly!", "Of course!", "Great question!", "Sure!", "As an AI" — BANNED.
- NO long explanations. Say what's needed, nothing more.
- NO bullet-point essays. Keep it conversational and tight.
- For coding: skip the theory. Give ONE correct code snippet + max 1 sentence of context. Done.
- If the user just chats — reply like a smart friend, 1-3 sentences max.
- Never repeat what the user said back to them.
- Never explain what you're about to do — just do it."""

    profile = get_user_profile()
    if profile:
        prompt += f"\n\nKnown about this user:\n{profile}\nApply these naturally."

    return prompt


# ── Groq text (no image) ───────────────────────────────────────────────────────
def ask_groq_text(prompt):
    global _conversation_history
    threading.Thread(target=_background_learn, args=(prompt,), daemon=True).start()
    try:
        from config import GROQ_TEXT_MODEL
        messages = [{"role": "system", "content": get_system_prompt()}]
        messages.extend(_conversation_history)
        messages.append({"role": "user", "content": prompt})

        response = groq_client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=messages,
            stream=True
        )

        full_response = ""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                yield content

        _conversation_history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": full_response}
        ])
        if len(_conversation_history) > MAX_HISTORY:
            del _conversation_history[:-MAX_HISTORY]

    except Exception as e:
        yield f"[Error] {e}"


# ── Groq vision (with screenshot) ─────────────────────────────────────────────
def ask_groq_vision(prompt, image):
    global _conversation_history
    threading.Thread(target=_background_learn, args=(prompt,), daemon=True).start()
    try:
        from config import GROQ_VISION_MODEL
        messages = [{"role": "system", "content": get_system_prompt()}]
        messages.extend(_conversation_history)

        user_content = [{"type": "text", "text": prompt}]

        if image:
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        messages.append({"role": "user", "content": user_content})

        response = groq_client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=messages,
            stream=True
        )

        full_response = ""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                yield content

        label = "[User + screen]" if image else "[User]"
        _conversation_history.extend([
            {"role": "user", "content": f"{label} {prompt}"},
            {"role": "assistant", "content": full_response}
        ])
        if len(_conversation_history) > MAX_HISTORY:
            del _conversation_history[:-MAX_HISTORY]

    except Exception as e:
        yield f"[Vision Error] {e}"


# ── Master router ──────────────────────────────────────────────────────────────
def think(user_text):
    from eyes import get_snapshot

    # Any of these words → user wants Jerry to look at their screen
    screen_keywords = [
        "screen", "look at", "see", "what is on", "read this", "this page",
        "this code", "what's on", "whats on", "show me", "can you see",
        "what do you see", "my screen", "here", "this window", "this tab",
        "what's this", "whats this", "this error", "this message", "what's that",
        "whats that", "open", "running", "this problem", "fix this", "debug",
        "help me with this", "what does this", "explain this", "why is this",
        "what's happening", "whats happening", "this warning", "this output"
    ]
    requires_screen = any(kw in user_text.lower() for kw in screen_keywords)

    if requires_screen:
        # Use the snapshot taken BEFORE the user started speaking (true context)
        screen = get_snapshot()
        if screen is None:
            print("[Brain] No snapshot available -- text only.")
            return ask_groq_text(user_text)
        print("[Brain] Sending screen snapshot to Groq Vision...")
        return ask_groq_vision(user_text, screen)
    else:
        print("[Brain] Text query -> Groq...")
        return ask_groq_text(user_text)