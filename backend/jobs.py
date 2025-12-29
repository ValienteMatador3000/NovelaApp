import threading
import uuid

jobs = {}

def crear_job(func, *args, **kwargs):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "estado": "procesando",
        "resultado": None,
        "error": None
    }

    def wrapper():
        try:
            resultado = func(*args, **kwargs)
            jobs[job_id]["estado"] = "completado"
            jobs[job_id]["resultado"] = resultado
        except Exception as e:
            jobs[job_id]["estado"] = "error"
            jobs[job_id]["error"] = str(e)

    threading.Thread(target=wrapper, daemon=True).start()
    return job_id


def job_audio(func, *args):
    job_id = crear_id()

    jobs[job_id] = {
        "estado": "procesando",
        "resultado": None,
        "error": None
    }

    def wrapper():
        try:
            resultado = func(*args)
            jobs[job_id]["estado"] = "completado"
            jobs[job_id]["resultado"] = resultado
        except Exception as e:
            jobs[job_id]["estado"] = "error"
            jobs[job_id]["error"] = str(e)

    Thread(target=wrapper, daemon=True).start()
    return job_id
