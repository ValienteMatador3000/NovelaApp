# -*- coding: utf-8 -*-
"""
motor_novela.py
Motor optimizado de scraping + traducción de novelas web
Diseñado para Render / FastAPI
"""

import os
import time
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


def ejecutar_motor(config):
    """
    Ejecuta scraping y traducción usando navegación secuencial por URL.
    Traduce por BLOQUES para máxima velocidad.
    """

    # =========================
    # Inicialización
    # =========================
    translator = GoogleTranslator(
        source=config.get("IDIOMA_ORIGEN", "auto"),
        target=config.get("IDIOMA_DESTINO", "es")
    )

    os.makedirs(config["CARPETA_SALIDA"], exist_ok=True)

    def contiene_chino(texto):
        return bool(re.search(r'[\u4e00-\u9fff]', texto))

    def traducir_bloque(texto, intentos=3):
        if not texto.strip():
            return ""
        for _ in range(intentos):
            try:
                traduccion = translator.translate(texto)
                if contiene_chino(traduccion):
                    raise Exception("Traducción incompleta")
                return traduccion
            except Exception:
                time.sleep(1)
        return texto  # fallback seguro

    def obtener_html(url):
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": config["URL_LIBRO"]
            }
            r = requests.get(url, headers=headers, timeout=20)
            r.encoding = config["SELECTORES"].get("ENCODING", "utf-8")
            return r.text if r.status_code == 200 else None
        except Exception:
            return None

    def extraer_capitulo(html, numero):
        soup = BeautifulSoup(html, "html.parser")

        # --- Título ---
        h1 = soup.select_one(config["SELECTORES"]["TITULO"])
        titulo_original = h1.get_text(strip=True) if h1 else f"Capítulo {numero}"
        titulo = traducir_bloque(titulo_original)

        # --- Contenido ---
        cont = soup.select_one(config["SELECTORES"]["CONTENIDO"])
        if not cont:
            return titulo, ""

        for basura in cont.select("script, ins, iframe, div.adBlock, div.gadBlock"):
            basura.decompose()

        parrafos = [
            p.get_text(strip=True)
            for p in cont.find_all("p")
            if len(p.get_text(strip=True)) > 1
        ]

        bloque = "\n\n".join(parrafos)
        texto_traducido = traducir_bloque(bloque)

        return titulo, texto_traducido

    # =========================
    # Proceso principal
    # =========================
    texto_final = f"NOVELA: {config['NOMBRE']}\n\n"

    url_inicial = config["URL_INICIAL"]
    dominio = config["DOMINIO"]

    # Extraer número de capítulo inicial
    m = re.search(r"/(\d+)_1\.html", url_inicial)
    if not m:
        return {
            "estado": "error",
            "mensaje": "No se pudo extraer el número de capítulo desde la URL"
        }

    cap_actual = int(m.group(1))
    base_url = url_inicial.split(f"/{cap_actual}_1.html")[0]

    limite = config.get("CANTIDAD_CAPITULOS")
    contador = 0

    while True:
        contador += 1
        url = f"{base_url}/{cap_actual}_1.html"

        html = obtener_html(url)
        if not html:
            break

        titulo, texto = extraer_capitulo(html, contador)

        texto_final += (
            f"\n\n{'=' * 40}\n{titulo}\n{'=' * 40}\n\n{texto}\n"
        )

        if limite and contador >= limite:
            break

        cap_actual += 1
        time.sleep(config.get("ESPERA_REQUEST", 0.5))

    # =========================
    # Guardado
    # =========================
    nombre_archivo = f"{config['NOMBRE']}_Caps_1_a_{contador}.txt"
    ruta_final = os.path.join(config["CARPETA_SALIDA"], nombre_archivo)

    with open(ruta_final, "w", encoding="utf-8") as f:
        f.write(texto_final)

    return {
        "estado": "ok",
        "capitulos_procesados": contador,
        "archivo": nombre_archivo,
        "ruta": ruta_final
    }

