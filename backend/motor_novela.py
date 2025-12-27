# -*- coding: utf-8 -*-
"""
motor_novela.py
Motor reutilizable de scraping + traducción de novelas web
"""

import os
import time
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


def ejecutar_motor(config):
    """
    Ejecuta el scraping y traducción de una novela
    usando navegación secuencial numérica.
    """

    # =========================
    # Inicialización
    # =========================
    translator = GoogleTranslator(
        source=config.get("IDIOMA_ORIGEN", "auto"),
        target=config["IDIOMA_DESTINO"]
    )

    def contiene_chino(texto):
        return bool(re.search(r'[\u4e00-\u9fff]', texto))

    def traducir_bloque_robusto(texto, max_retries=3):
        for _ in range(max_retries):
            try:
                if not texto.strip():
                    return ""
                traduccion = translator.translate(texto)
                if contiene_chino(traduccion):
                    raise Exception("Traducción inválida")
                return traduccion
            except Exception:
                time.sleep(1.2)
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
            r.encoding = config["SELECTORES"]["ENCODING"]
            return r.text if r.status_code == 200 else None
        except Exception:
            return None

    def extraer_datos(html, num_cap):
        soup = BeautifulSoup(html, "html.parser")

        # Título
        h1 = soup.select_one(config["SELECTORES"]["TITULO"])
        titulo_orig = h1.get_text(strip=True) if h1 else f"Capítulo {num_cap}"
        titulo_es = traducir_bloque_robusto(titulo_orig)

        # Contenido
        cont = soup.select_one(config["SELECTORES"]["CONTENIDO"])
        if not cont:
            return titulo_es, ""

        for basura in cont.select("div.gadBlock, div.adBlock, script, ins, iframe"):
            basura.decompose()

        texto = ""
        for p in cont.find_all("p"):
            linea = p.get_text(strip=True)
            if len(linea) < 2:
                continue
            texto += traducir_bloque_robusto(linea) + "\n\n"
            time.sleep(config["ESPERA_TRAD"])

        return titulo_es, texto

    # =========================
    # Proceso principal
    # =========================
    os.makedirs(config["CARPETA_SALIDA"], exist_ok=True)

    texto_volumen = f"NOVELA: {config['NOMBRE']}\n\n"

    url_inicial = config["URL_INICIAL"]
    contador = 0

    # Extraer número de capítulo inicial
    match = re.search(r"/(\d+)_1\.html", url_inicial)
    if not match:
        return {
            "estado": "error",
            "mensaje": "No se pudo extraer el número de capítulo de la URL inicial"
        }

    cap_num = int(match.group(1))
    base_url = url_inicial.split(f"/{cap_num}_1.html")[0]

    while True:
        contador += 1
        url = f"{base_url}/{cap_num}_1.html"

        html = obtener_html(url)
        if not html:
            break

        titulo, contenido = extraer_datos(html, contador)

        texto_volumen += (
            f"\n\n{'=' * 40}\n"
            f"{titulo}\n"
            f"{'=' * 40}\n\n"
            f"{contenido}\n"
        )

        # Límite de capítulos
        if (
            config.get("CANTIDAD_CAPITULOS") is not None
            and contador >= config["CANTIDAD_CAPITULOS"]
        ):
            break

        cap_num += 1
        time.sleep(config["ESPERA_REQUEST"])

    nombre_archivo = f"{config['NOMBRE']}_Caps_1_a_{contador}.txt"
    ruta_final = os.path.join(config["CARPETA_SALIDA"], nombre_archivo)

    with open(ruta_final, "w", encoding="utf-8") as f:
        f.write(texto_volumen)

    return {
        "estado": "ok",
        "capitulos_procesados": contador,
        "archivo": nombre_archivo,
        "ruta": ruta_final
    }

