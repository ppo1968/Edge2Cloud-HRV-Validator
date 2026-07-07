import re
from pathlib import Path

# ======================================================
# CONFIGURACIÓN GLOBAL DEL PROYECTO
# ======================================================


# ======================================================
# RUTAS Y CARPETAS ESTÁNDAR
# ======================================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATOS_DIR_NAME = "Datos"
RESULTADOS_DIR_NAME = "Resultados"
ASSETS_DIR_NAME = "assets"
SHARED_IMAGES_SUBDIR = "images"

RESULTADOS_DIR = SCRIPT_DIR / RESULTADOS_DIR_NAME
ASSETS_DIR = SCRIPT_DIR / ASSETS_DIR_NAME
SHARED_IMAGES_DIR = ASSETS_DIR / SHARED_IMAGES_SUBDIR

PARTICIPANTES_DIR_NAMES = (
    "Datos",
    "DATOS",
    "datos",
    "Dato",
    "DATO",
    "dato",
    "analisis de participantes",
    "análisis de participantes",
    "analisis_participantes",
    "participantes",
)

IMAGE_EXTENSIONS = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp")

DATE_PATTERNS = [
    re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})\s+at\s+(?P<time>\d{2}\.\d{2}\.\d{2})", re.IGNORECASE),
    re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})[ _-]+(?P<time>\d{2}[\.:\-]\d{2}[\.:\-]\d{2})", re.IGNORECASE),
    re.compile(r"(?P<date>\d{2}[\-\.]\d{2}[\-\.]\d{4})[ _-]+(?P<time>\d{2}[\.:\-]\d{2}[\.:\-]\d{2})", re.IGNORECASE),
    re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(?P<date>\d{2}[\-\.]\d{2}[\-\.]\d{4})", re.IGNORECASE),
]

SESSION_GROUP_GAP_SECONDS = 90
