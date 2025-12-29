# backend/tts_edge.py
import os
import asyncio
from edge_tts import Communicate
from pydub import AudioSegment


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
# GENERAR AUDIO EDGE (async)
# =========================

async def generar_audio_edge(texto, salida_mp3, voz):
    communicate = Communicate(texto, voz)
    await communicate.save(salida_mp3)


# =========================
# FUNCIÓN NÚCLEO (AQUÍ)
# =========================

def generar_audiolibro(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    """
    Genera un audiolibro MP3 a partir de un archivo TXT.
    """

    if not os.path.exists(txt_path):
        raise FileNotFoundError("Archivo TXT no encontrado")

    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read()

    bloques = dividir_texto(texto)

    if not bloques:
        raise Exception("El texto no contiene contenido válido")

    audios_temporales = []

    for i, bloque in enumerate(bloques, start=1):
        print(f"🎧 Generando audio {i}/{len(bloques)}")

        tmp_mp3 = salida_mp3.replace(".mp3", f"_part{i}.mp3")
        asyncio.run(generar_audio_edge(bloque, tmp_mp3, voz))
        audios_temporales.append(tmp_mp3)

    # =========================
    # UNIR AUDIOS
    # =========================

    audio_final = AudioSegment.empty()

    for a in audios_temporales:
        audio_final += AudioSegment.from_mp3(a)

    audio_final.export(salida_mp3, format="mp3")

    # Limpieza
    for a in audios_temporales:
        os.remove(a)

    return {
        "estado": "ok",
        "bloques": len(bloques),
        "archivo_audio": os.path.basename(salida_mp3),
        "ruta": salida_mp3
    }


# =========================
# WRAPPER SÍNCRONO (FASTAPI)
# =========================

def generar_audio_sync(txt_path, salida_mp3, voz="es-MX-JorgeNeural"):
    """
    Wrapper síncrono para usar desde FastAPI / jobs
    """
    return generar_audiolibro(txt_path, salida_mp3, voz)

