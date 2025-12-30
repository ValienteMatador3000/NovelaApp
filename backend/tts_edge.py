# backend/tts_edge.py
import os
import asyncio
from edge_tts import Communicate


# =========================
# DIVISIÓN SEGURA DEL TEXTO
# =========================

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


# =========================
# FUNCIÓN ASYNC INTERNA
# =========================

async def _generar_audio_async(bloques, salida_mp3, voz):
    """
    Genera UN SOLO archivo MP3 con múltiples llamadas secuenciales
    """
    communicate = Communicate("", voz)

    # Abrimos el archivo una sola vez
    with open(salida_mp3, "wb") as f:
        for i, bloque in enumerate(bloques, start=1):
            print(f"🎧 Generando audio bloque {i}/{len(bloques)}")

            communicate.text = bloque

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])


# =========================
# FUNCIÓN NÚCLEO (SYNC)
# =========================

def generar_audiolibro(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    """
    Genera un audiolibro MP3 a partir de un TXT (EDGE TTS)
    """

    if not os.path.exists(txt_path):
        raise FileNotFoundError("Archivo TXT no encontrado")

    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read()

    bloques = dividir_texto(texto)

    if not bloques:
        raise Exception("El texto está vacío o no es válido")

    # Ejecutar async de forma segura
    asyncio.run(_generar_audio_async(bloques, salida_mp3, voz))

    return {
        "estado": "ok",
        "bloques": len(bloques),
        "archivo_audio": os.path.basename(salida_mp3),
        "ruta": salida_mp3
    }


# =========================
# WRAPPER FASTAPI
# =========================

def generar_audio_sync(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    return generar_audiolibro(txt_path, salida_mp3, voz)

