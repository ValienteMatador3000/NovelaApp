# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.motor_novela import ejecutar_motor
from backend.tts_edge import generar_audio_sync
from backend.jobs import crear_job, jobs

import os

# =========================
# APP
# =========================

app = FastAPI(
    title="Motor de Novelas Web",
    description="API para scraping, traducción y audiolibros",
    version="1.1"
)

# =========================
# 🔓 CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # desarrollo / GitHub Pages
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
# ENDPOINT: PROCESAR NOVELA (JOB)
# =========================

@app.post("/procesar")
def procesar_novela(req: NovelaRequest):

    carpeta_salida = os.path.join("salida", req.nombre)
    os.makedirs(carpeta_salida, exist_ok=True)

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

        "CARPETA_SALIDA": carpeta_salida
    }

    job_id = crear_job(ejecutar_motor, config)

    return {
        "estado": "ok",
        "mensaje": "Proceso iniciado en segundo plano",
        "job_id": job_id
    }


# =========================
# ENDPOINT: ESTADO DEL JOB
# =========================

@app.get("/estado/{job_id}")
def estado_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    return jobs[job_id]


# =========================
# ENDPOINT: GENERAR AUDIOLIBRO (JOB)
# =========================

@app.post("/audiolibro")
def generar_audiolibro(req: AudioRequest):

    txt_path = os.path.join("salida", req.nombre, req.archivo_txt)

    if not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="Archivo TXT no encontrado")

    mp3_name = req.archivo_txt.replace(".txt", ".mp3")
    mp3_path = os.path.join("salida", req.nombre, mp3_name)

    job_id = crear_job(
        generar_audio_sync,
        txt_path,
        mp3_path
    )

    return {
        "estado": "ok",
        "mensaje": "Generación de audiolibro iniciada",
        "job_id": job_id,
        "archivo_mp3": mp3_name
    }


# =========================
# ENDPOINT: DESCARGA TXT
# =========================

@app.get("/descargar/{nombre}/{archivo}")
def descargar_archivo(nombre: str, archivo: str):

    ruta = os.path.join("salida", nombre, archivo)

    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media_type = "text/plain"
    if archivo.endswith(".mp3"):
        media_type = "audio/mpeg"

    return FileResponse(
        path=ruta,
        filename=archivo,
        media_type=media_type
    )


# =========================
# ENDPOINT: ROOT
# =========================

@app.get("/")
def root():
    return {
        "estado": "ok",
        "mensaje": "API de novelas y audiolibros activa"
    }

