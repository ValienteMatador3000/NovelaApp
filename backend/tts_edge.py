# backend/tts_edge.py
import asyncio
import edge_tts
import os

# Voz por defecto (puedes cambiarla luego desde la UI)
VOICE_ES = "es-MX-JorgeNeural"


# -------------------------------
# FUNCIÓN ASÍNCRONA (EDGE TTS)
# -------------------------------
async def generar_audio(txt_path, mp3_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read()

    if not texto.strip():
        raise Exception("El texto está vacío")

    communicate = edge_tts.Communicate(
        text=texto,
        voice=VOICE_ES,
        rate="+0%",
        volume="+0%"
    )

    await communicate.save(mp3_path)


# -------------------------------
# WRAPPER SÍNCRONO (FASTAPI)
# -------------------------------
def generar_audio_sync(txt_path, mp3_path):
    """
    Wrapper para poder llamar Edge TTS desde FastAPI
    sin problemas de event loop.
    """
    asyncio.run(generar_audio(txt_path, mp3_path))


#==================================

def dividir_texto(texto, max_chars=1800):
    bloques = []
    actual = ""

    for linea in texto.split("\n"):
        if len(actual) + len(linea) > max_chars:
            if actual.strip():
                bloques.append(actual.strip())
            actual = linea + "\n"
        else:
            actual += linea + "\n"

    if actual.strip():
        bloques.append(actual.strip())

    return bloques


