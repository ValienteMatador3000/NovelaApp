# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from backend.motor_novela import ejecutar_motor
import os

app = FastAPI(
    title="Motor de Novelas Web",
    description="API para scraping y traducción de novelas",
    version="1.0"
)

# =========================
# MODELO DE ENTRADA
# =========================

class NovelaRequest(BaseModel):
    nombre: str
    url_inicial: str
    url_libro: str
    dominio: str
    capitulos: int = 5


# =========================
# ENDPOINT PRINCIPAL
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

    resultado = ejecutar_motor(config)

    return {
        "mensaje": "Proceso completado",
        "resultado": resultado
    }


# =========================
# ENDPOINT DE PRUEBA
# =========================

@app.get("/")
def root():
    return {
        "estado": "ok",
        "mensaje": "API de novelas activa"
    }
