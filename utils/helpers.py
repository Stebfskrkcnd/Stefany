import json
import os
import subprocess
import logging
import traceback
import json, os, requests, logging
import base64

GITHUB_API = "https://api.github.com"
REPO = "Stebfskrkcnd/Stefany"  # tu repo en GitHub
BRANCH = "main"
TOKEN = os.getenv("GIT_TOKEN")

def save_json(path, data):
    try:
        # Guarda el archivo local temporalmente
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.info(f"✅ JSON guardado localmente en {os.path.abspath(path)}")
    
        # Lee contenido del archivo
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Codifica a base64
        import base64
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Obtiene SHA actual del archivo en GitHub
        api_url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
        headers = {"Authorization": f"token {TOKEN}"}
        r = requests.get(api_url, headers=headers)
        sha = r.json().get("sha") if r.ok else None

        # Prepara payload para crear o actualizar
        payload = {
            "message": f"update {path}",
            "content": content_b64,
            "branch": BRANCH
        }
        if sha:
            payload["sha"] = sha

        # Hace push vía API
        r = requests.put(api_url, headers=headers, json=payload)
        if r.ok:
            logging.info(f"✅ Push a GitHub de {path} exitoso")
        else:
            logging.error(f"❌ Error al hacer push: {r.text}")

    except Exception as e:
        logging.error("❌ Error guardando y haciendo push:")
        logging.error(traceback.format_exc())

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"⚠️ Archivo no encontrado: {path}")
        return default if default is not None else []
    except Exception as e:
        logging.error(f"❌ Error leyendo {path}: {e}")
        return default if default is not None else []

def get_encabezado():
    return {
        "fileid": os.getenv("ENCABEZADO_FILEID", ""),
        "caption": os.getenv("ENCABEZADO_CAPTION", "")
    }
    
def limpiar_canales_inactivos():
    canales = load_json("data/channels.json")
    canales_filtrados = [canal for canal in canales if canal.get("activo", True)]
    save_json("data/channels.json", canales_filtrados)

def git_push(mensaje_commit="Cambios desde el bot", archivos=["channels.json", "blacklist.json", "estado.json"]):
    GIT_TOKEN = os.getenv("GIT_TOKEN", "")
    REPO = os.getenv("GIT_REPO", "")
    USER = os.getenv("GIT_USER", "")

    if not GIT_TOKEN or not REPO or not USER:
        logging.error("⚠️  Faltan variables de entorno para el push a GitHub.")
        return

    headers = {
        "Authorization": f"Bearer {GIT_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    for archivo in archivos:
        ruta = f"data/{archivo}"
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()

        contenido_base64 = base64.b64encode(contenido.encode("utf-8")).decode("utf-8")
        api_url = f"https://api.github.com/repos/{USER}/{REPO}/contents/data/{archivo}"

        # Obtener SHA actual
        r_get = requests.get(api_url, headers=headers)
        if r_get.ok:
            sha = r_get.json().get("sha")
        else:
            sha = None  # Si el archivo no existe, se hace sin SHA

        payload = {
            "message": mensaje_commit,
            "content": contenido_base64,
            "branch": "main"
        }

        if sha:
            payload["sha"] = sha

        try:
            r_put = requests.put(api_url, headers=headers, json=payload)
            if r_put.ok:
                logging.info(f"✅ Push a GitHub de {archivo} exitoso")
            else:
                logging.error(f"❌ Error al hacer push de {archivo}: {r_put.text}")
        except Exception as e:
            logging.error(f"❌ Excepción en el push de {archivo}: {e}")