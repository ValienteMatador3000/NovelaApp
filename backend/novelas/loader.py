# backend/novelas/loader.py
import json
import os

BASE_DIR = os.path.dirname(__file__)

CATALOGO_PATH = os.path.join(BASE_DIR, "catalogo.json")
PRESETS_PATH = os.path.join(BASE_DIR, "presets.json")


def cargar_catalogo():
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_presets():
    with open(PRESETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_novela(novela_id):
    catalogo = cargar_catalogo()
    presets = cargar_presets()

    if novela_id not in catalogo:
        raise ValueError("Novela no existe en el catálogo")

    if novela_id not in presets:
        raise ValueError("Novela sin preset técnico")

    return {
        **catalogo[novela_id],
        "preset": presets[novela_id]
    }


def listar_novelas():
    catalogo = cargar_catalogo()
    return list(catalogo.values())
