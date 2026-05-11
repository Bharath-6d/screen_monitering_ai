import queue
import threading
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard

from config import SAMPLE_RATE, CHANNELS, MODEL_SIZE
from brain import think
from mouth import speak

HOTKEY_KEYS = {keyboard.Key.alt_l, keyboard.KeyCode.from_char('k')}
SILENCE_SECONDS_AFTER_RELEASE = 0.25

model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

audio_q = queue.Queue()
recording = False
frames = []
stream = None
pressed = set()
lock = threading.Lock()
current_session_id = 0

# Guard: ensure begin_recording only runs ONCE per key-hold, not on every key-repeat
_session_started = False


def audio_callback(indata, frames_count, time_info, status):
    if recording:
        audio_q.put(indata.copy())


def start_stream():
    global stream
    if stream is None:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=audio_callback,
        )
        stream.start()


def stop_stream():
    global stream
    if stream:
        stream.stop()
        stream.close()
        stream = None


def begin_recording():
    global recording, frames, current_session_id, _session_started

    # KEY FIX: on_press fires repeatedly while key is held (OS key-repeat).
    # Only run once per hold using _session_started guard.
    if _session_started:
        return
    _session_started = True

    from mouth import stop_speaking
    from ui import set_listening, hide_ui
    from eyes import snapshot

    # Take snapshot ONCE, right now, before anything steals screen focus
    snapshot()

    stop_speaking()
    hide_ui()

    with lock:
        current_session_id += 1
        frames = []
        recording = True
        start_stream()
        set_listening(True)
        print("[Jerry] Listening...")


def end_recording():
    global recording, _session_started
    _session_started = False   # Reset so next ALT+K press works

    with lock:
        if recording:
            time.sleep(SILENCE_SECONDS_AFTER_RELEASE)
            recording = False
            print("[Jerry] Processing...")

            while not audio_q.empty():
                frames.append(audio_q.get())

            if frames:
                audio = np.concatenate(frames, axis=0).astype(np.int16)
                session_id = current_session_id
                threading.Thread(
                    target=transcribe_and_respond,
                    args=(audio, session_id),
                    daemon=True
                ).start()
            else:
                from ui import set_listening
                set_listening(False)


def transcribe_and_respond(audio_int16, session_id):
    if session_id != current_session_id:
        return

    audio_f32 = audio_int16.flatten().astype(np.float32) / 32768.0
    segments, _ = model.transcribe(audio_f32, language="en")
    text = "".join([seg.text for seg in segments]).strip()

    if session_id != current_session_id:
        return

    from ui import set_listening
    set_listening(False)

    if text:
        reply = think(text)

        if session_id != current_session_id:
            return

        speak(reply, user_text=text)
    else:
        print("[Jerry] (No speech detected)")


def on_press(key):
    pressed.add(key)
    if HOTKEY_KEYS.issubset(pressed):
        begin_recording()   # guarded inside — safe to call on every repeat


def on_release(key):
    if key in pressed:
        pressed.remove(key)
    if not HOTKEY_KEYS.issubset(pressed):
        end_recording()


def run_ears():
    print("Hold ALT+K to talk")
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    try:
        while listener.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_stream()
        listener.stop()