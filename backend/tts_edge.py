# backend/tts_edge.py
import asyncio
import edge_tts
import os

VOICE_ES = "es-MX-JorgeNeural"  # voz masculina
# otras opciones:
# es-ES-AlvaroNeural
# es-MX-DaliaNeural

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
