import asyncio
import edge_tts
import pygame
import io
import re

pygame.mixer.init()

_interrupted = False


def stop_speaking():
    global _interrupted
    _interrupted = True
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()


async def speak_async(generator_or_text, user_text=""):
    global _interrupted
    _interrupted = False

    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

    audio_queue = asyncio.Queue()

    async def audio_player_task():
        try:
            while not _interrupted:
                try:
                    audio_file = await asyncio.wait_for(audio_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                if _interrupted:
                    audio_queue.task_done()
                    continue

                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not _interrupted:
                    await asyncio.sleep(0.05)

                if _interrupted:
                    pygame.mixer.music.stop()

                audio_queue.task_done()
        except asyncio.CancelledError:
            pass

    player_task = asyncio.create_task(audio_player_task())

    async def synthesize_and_queue(text):
        if _interrupted:
            return
        text = re.sub(r'[*#_~]', '', text).strip()
        if not text:
            return
        try:
            from config import VOICE
            communicate = edge_tts.Communicate(text, VOICE)
            audio_bytes = b""
            async for chunk in communicate.stream():
                if _interrupted:
                    return
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            if audio_bytes and not _interrupted:
                await audio_queue.put(io.BytesIO(audio_bytes))
        except Exception as e:
            print(f"[TTS Error] {e}")
            try:
                clean = text.replace("'", "").replace('"', "")
                script = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{clean}')"
                proc = await asyncio.create_subprocess_exec(
                    "powershell", "-Command", script, creationflags=0x08000000
                )
                await proc.communicate()
            except Exception as pe:
                print(f"[Offline TTS Error] {pe}")

    from ui import set_user_text, clear_response, append_response

    # Show the user's query in the UI header
    if user_text:
        set_user_text(user_text)

    clear_response()

    buffer = ""
    full_response = ""

    if isinstance(generator_or_text, str):
        full_response = generator_or_text
        append_response(full_response)
        await synthesize_and_queue(full_response)
    else:
        for chunk in generator_or_text:
            if _interrupted:
                break
            append_response(chunk)
            full_response += chunk
            buffer += chunk

            match = re.search(r'([.!?\n])\s+', buffer)
            while match and not _interrupted:
                end_idx = match.end()
                sentence = buffer[:end_idx]
                await synthesize_and_queue(sentence)
                buffer = buffer[end_idx:]
                match = re.search(r'([.!?\n])\s+', buffer)

        if buffer.strip() and not _interrupted:
            await synthesize_and_queue(buffer)

    while not audio_queue.empty() and not _interrupted:
        await asyncio.sleep(0.1)

    while pygame.mixer.music.get_busy() and not _interrupted:
        await asyncio.sleep(0.1)

    player_task.cancel()


def speak(text, user_text=""):
    asyncio.run(speak_async(text, user_text))