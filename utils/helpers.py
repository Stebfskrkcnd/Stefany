import json
import os
import logging

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"✅ JSON guardado en {os.path.abspath(path)}")
    except Exception as e:
        logging.error(f"❌ Error guardando {path}: {e}")

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