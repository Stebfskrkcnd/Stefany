import os
import json
from utils.helpers import load_json

USUARIOS_AUTORIZADOS = load_json("data/autorizados.json")
# Cargar token
BOT_TOKEN = os.getenv("BOT_TOKEN")
PATH_BLACKLIST_JSON = "data/blacklist.json"
TOKEN = os.getenv("GIT_TOKEN", "")

print("TOKEN OK:", TOKEN[:8])  # Solo para verificar que lo cargó

# Cargar usuarios autorizados desde string: "12345;67890"
USUARIOS_AUTORIZADOS = [
    int(uid) for uid in os.getenv("USUARIOS_AUTORIZADOS", "").split(";") if uid.strip().isdigit()
]

# Cargar canales fijos desde string JSON (idealmente set en Railway como texto plano)
try:
    CANALES_FIJOS = json.loads(os.getenv("CANALES_FIJOS", "[]"))
except json.JSONDecodeError:
    CANALES_FIJOS = []
    
ENCABEZADO_FILEID = os.getenv("ENCABEZADO_FILEID", "")
ENCABEZADO_CAPTION = os.getenv("ENCABEZADO_CAPTION", "")

# Zona horaria
ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/New_York")