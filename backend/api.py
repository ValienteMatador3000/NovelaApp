# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.motor_novela import ejecutar_motor
from backend.tts_edge import generar_audio_sync
from backend.jobs import crear_job, jobs

import os
import json

# =========================
# APP
# =========================

app = FastAPI(
    title="Motor de Novelas Web",
    description="API para scraping, traducción y audiolibros",
    version="1.2"
)

# =========================
# 🔓 CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELOS
# =========================

class NovelaRequest(BaseModel):
    nombre: str
    url_inicial: str
    url_libro: str
    dominio: str
    capitulos: int = 5


class AudioRequest(BaseModel):
    nombre: str
    archivo_txt: str


# =========================
# ENDPOINT: CATÁLOGO
# =========================

@app.get("/novelas")
def listar_novelas():
    ruta = os.path.join(
        os.path.dirname(__file__),
        "novelas",
        "catalogo.json"
    )

    if not os.path.exists(ruta):
        raise HTTPException(500, "catalogo.json no encontrado")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(500, f"Error leyendo catalogo.json: {e}")

    return {
        "estado": "ok",
        "novelas": data
    }


# =========================
# ENDPOINT: PROCESAR NOVELA
# =========================

@app.post("/procesar")
def procesar_novela(req: NovelaRequest):

    carpeta = os.path.join("salida", req.nombre)
    os.makedirs(carpeta, exist_ok=True)

    config = {
        "NOMBRE": req.nombre,
        "URL_INICIAL": req.url_inicial,
        "URL_LIBRO": req.url_libro,
        "DOMINIO": req.dominio,
        "CANTIDAD_CAPITULOS": req.capitulos,
        "SELECTORES": {
            "TITULO": "div.chapter-content > h1",
            "CONTENIDO": "div.chapter-content div.content",
            "ENCODING": "utf-8"
        },
        "IDIOMA_ORIGEN": "zh-TW",
        "IDIOMA_DESTINO": "es",
        "ESPERA_REQUEST": 1.5,
        "ESPERA_TRAD": 0.6,
        "CARPETA_SALIDA": carpeta
    }

    job_id = crear_job(ejecutar_motor, config)

    return {
        "estado": "ok",
        "job_id": job_id
    }


# =========================
# ENDPOINT: ESTADO JOB
# =========================

@app.get("/estado/{job_id}")
def estado_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")

    return jobs[job_id]


# =========================
# ENDPOINT: DESCARGA TXT / MP3
# =========================

@app.get("/descargar/{nombre}/{archivo}")
def descargar(nombre: str, archivo: str):

    ruta = os.path.join("salida", nombre, archivo)

    if not os.path.exists(ruta):
        raise HTTPException(404, "Archivo no encontrado")

    media = "audio/mpeg" if archivo.endswith(".mp3") else "text/plain"

    return FileResponse(
        path=ruta,
        filename=archivo,
        media_type=media
    )


# =========================
# ENDPOINT: AUDIOLIBRO
# =========================

@app.post("/audiolibro")
def generar_audiolibro(req: AudioRequest):

    txt = os.path.join("salida", req.nombre, req.archivo_txt)

    if not os.path.exists(txt):
        raise HTTPException(404, "Archivo TXT no encontrado")

    mp3 = req.archivo_txt.replace(".txt", ".mp3")
    mp3_path = os.path.join("salida", req.nombre, mp3)

    job_id = crear_job(
        generar_audio_sync,
        txt,
        mp3_path
    )

    return {
        "estado": "ok",
        "job_id": job_id,
        "archivo_mp3": mp3
    }


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {
        "estado": "ok",
        "mensaje": "API activa"
    }

