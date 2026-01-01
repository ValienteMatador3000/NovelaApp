# api.py
from fastapi import FastAPI, HTTPException, Query
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
    version="1.4"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.abspath("salida")

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
# CATÁLOGO
# =========================

@app.get("/novelas")
def listar_novelas():
    ruta = os.path.join(os.path.dirname(__file__), "novelas", "catalogo.json")
    if not os.path.exists(ruta):
        raise HTTPException(500, "catalogo.json no encontrado")

    with open(ruta, "r", encoding="utf-8") as f:
        return {"estado": "ok", "novelas": json.load(f)}

# =========================
# PROCESAR NOVELA
# =========================

@app.post("/procesar")
def procesar(req: NovelaRequest):
    carpeta = os.path.join(BASE_DIR, req.nombre)
    os.makedirs(carpeta, exist_ok=True)

    config = {
        "NOMBRE": req.nombre,
        "URL_INICIAL": req.url_inicial,
        "URL_LIBRO": req.url_libro,
        "DOMINIO": req.dominio,
        "CANTIDAD_CAPITULOS": req.capitulos,
        "CARPETA_SALIDA": carpeta
    }

    job_id = crear_job(ejecutar_motor, config)
    return {"estado": "ok", "job_id": job_id}

# =========================
# ESTADO JOB
# =========================

@app.get("/estado/{job_id}")
def estado(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")
    return jobs[job_id]

# =========================
# DESCARGA SEGURA (FIX DEFINITIVO)
# =========================

@app.get("/descargar")
def descargar(ruta: str = Query(...)):
    ruta_abs = os.path.abspath(os.path.normpath(ruta))

    # 🔐 Verificación REAL de seguridad
    if os.path.commonpath([ruta_abs, BASE_DIR]) != BASE_DIR:
        raise HTTPException(status_code=400, detail="Ruta inválida")

    if not os.path.exists(ruta_abs):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media = "audio/mpeg" if ruta_abs.endswith(".mp3") else "text/plain"

    return FileResponse(
        path=ruta_abs,
        filename=os.path.basename(ruta_abs),
        media_type=media
    )

# =========================
# AUDIOLIBRO
# =========================

@app.post("/audiolibro")
def audiolibro(req: AudioRequest):
    txt = os.path.join(BASE_DIR, req.nombre, req.archivo_txt)
    if not os.path.exists(txt):
        raise HTTPException(404, "TXT no encontrado")

    mp3 = txt.replace(".txt", ".mp3")
    job_id = crear_job(generar_audio_sync, txt, mp3)

    return {
        "estado": "ok",
        "job_id": job_id,
        "archivo_mp3": os.path.basename(mp3)
    }

@app.get("/")
def root():
    return {"estado": "ok", "mensaje": "API activa"}

