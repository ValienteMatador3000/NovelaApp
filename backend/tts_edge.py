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
# GENERACIÓN ASYNC (EDGE TTS)
# =========================

async def _generar_audio_async(txt_path, salida_mp3, voz):
    if not os.path.exists(txt_path):
        raise FileNotFoundError("Archivo TXT no encontrado")

    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    bloques = dividir_texto(texto)

    if not bloques:
        raise Exception("El texto no contiene contenido válido")

    # Crear carpeta destino si no existe
    os.makedirs(os.path.dirname(salida_mp3), exist_ok=True)

    # Borramos el mp3 si ya existía
    if os.path.exists(salida_mp3):
        os.remove(salida_mp3)

    for i, bloque in enumerate(bloques, start=1):
        print(f"🎧 TTS bloque {i}/{len(bloques)}")

        communicate = Communicate(
            bloque,
            voz,
            rate="+0%",
            volume="+0%"
        )

        # append=True → escribe todo en el MISMO mp3
        await communicate.save(salida_mp3, append=True)

    return {
        "estado": "ok",
        "bloques": len(bloques),
        "archivo_audio": os.path.basename(salida_mp3),
        "ruta": salida_mp3
    }


# =========================
# WRAPPER SÍNCRONO (FASTAPI / JOBS)
# =========================

def generar_audio_sync(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    """
    Wrapper síncrono para FastAPI / sistema de jobs
    """
    return asyncio.run(
        _generar_audio_async(txt_path, salida_mp3, voz)
    )

