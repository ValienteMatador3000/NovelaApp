# backend/tts_edge.py
import os
import asyncio
from edge_tts import Communicate


# =========================
# LIMPIEZA DEL TEXTO
# =========================

def preparar_texto_para_tts(texto: str) -> str:
    """
    Limpia y adapta el texto para TTS largo
    """
    # Pausas naturales
    texto = texto.replace("\n\n", ".\n")
    texto = texto.replace("\n", ".\n")

    # Evitar símbolos raros
    texto = texto.replace("=", "")
    texto = texto.replace("—", ",")
    texto = texto.replace("…", "...")

    return texto.strip()


# =========================
# FUNCIÓN ASYNC ÚNICA
# =========================

async def _generar_audio_async(texto: str, salida_mp3: str, voz: str):
    communicate = Communicate(texto, voz)

    with open(salida_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


# =========================
# FUNCIÓN PRINCIPAL
# =========================

def generar_audiolibro(
    txt_path: str,
    salida_mp3: str,
    voz: str = "es-MX-JorgeNeural"
):
    """
    Genera un audiolibro MP3 usando Edge TTS
    (un solo stream, estable en Render)
    """

    if not os.path.exists(txt_path):
        raise FileNotFoundError("Archivo TXT no encontrado")

    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read()

    if not texto.strip():
        raise Exception("El texto está vacío")

    texto_tts = preparar_texto_para_tts(texto)

    # Ejecutar async de forma segura
    asyncio.run(_generar_audio_async(texto_tts, salida_mp3, voz))

    return {
        "estado": "ok",
        "archivo_audio": os.path.basename(salida_mp3),
        "ruta": salida_mp3
    }


# =========================
# WRAPPER FASTAPI
# =========================

def generar_audio_sync(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    return generar_audiolibro(txt_path, salida_mp3, voz)

