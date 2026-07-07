from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.edge.ocr_edge import process_edge_images
from src.sessions.session_manager import run_session_manager
from src.importers.auto_importer import scan_and_import_raw

VERSION = "0.4.4_importador_universal"
ROOT = Path(__file__).resolve().parent

OFFICIAL_DIRS = [
    "config",
    "src/edge", "src/cloud", "src/wimu", "src/spro", "src/hrv", "src/compare", "src/reports", "src/sessions", "src/importers", "src/utils",
    "data/input/edge_images", "data/input/cloud_raw", "data/input/wimu_raw", "data/input/spro_export",
    "data/processed/edge", "data/processed/cloud", "data/processed/wimu", "data/processed/spro", "data/processed/raw_imports",
    "data/sessions",
    "results/intra", "results/inter", "results/figures", "results/reports", "results/excel",
    "docs", "tests",
]

LEGACY_NAMES = {
    "datos", "resultados", "datos_cloud",
    "01_EDGE_APP_imagenes", "01_EDGE_OCR_calculado", "02_EDGE_APP_OCR_calculado",
    "02_CLOUD_raw", "03_CLOUD_raw_app", "03_SPRO_calculado",
    "04_CLOUD_raw_calculado", "05_WIMU_raw", "06_WIMU_raw_calculado", "07_SPRO_calculado",
}

HRV_VARIABLES = [
    "HR_bpm", "RMSSD_ms", "LnRMSSD", "RR_medio_ms", "SDNN_ms", "SD1_ms", "SD2_ms",
    "indice_estres", "frecuencia_respiratoria_resp_min", "LF_ms2", "HF_ms2",
    "LF_nu_pct", "HF_nu_pct", "LF_HF_ratio",
]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def ensure_dirs() -> None:
    for rel in OFFICIAL_DIRS:
        p = ROOT / rel
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    log("Estructura oficial creada/verificada")


def audit_legacy() -> list[Path]:
    """Detecta carpetas antiguas sin duplicar padre e hijos.

    Regla de seguridad:
    - Si existe una carpeta antigua de nivel superior, se mueve completa.
    - No se añaden sus subcarpetas a la lista para evitar errores al mover.
    """
    legacy: list[Path] = []

    for child in ROOT.iterdir():
        if not child.is_dir():
            continue
        if child.name in {"data", "results", "src", "config", "docs", "tests", "_legacy_backup", ".git"}:
            continue
        if child.name in LEGACY_NAMES:
            legacy.append(child)

    # Si la carpeta datos no está marcada como legacy por algún motivo,
    # entonces se inspeccionan sus subcarpetas antiguas.
    datos = ROOT / "datos"
    if datos.exists() and datos.is_dir() and datos not in legacy:
        for child in datos.iterdir():
            if child.is_dir() and child.name in LEGACY_NAMES:
                legacy.append(child)

    # Eliminar cualquier hijo cuyo padre ya esté en la lista.
    cleaned: list[Path] = []
    for p in sorted(set(legacy), key=lambda x: len(x.parts)):
        if not any(parent in p.parents for parent in cleaned):
            cleaned.append(p)
    return cleaned

def print_audit() -> None:
    legacy = audit_legacy()
    if not legacy:
        log("No se han detectado carpetas antiguas")
        return
    log("Carpetas antiguas detectadas")
    for p in legacy:
        print(" -", p.relative_to(ROOT))
    print("\nPara moverlas a _legacy_backup ejecuta:")
    print("python main.py --clean-legacy")


def clean_legacy() -> None:
    ensure_dirs()
    legacy = audit_legacy()
    if not legacy:
        log("No hay carpetas antiguas que limpiar")
        return

    backup = ROOT / "_legacy_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup.mkdir(parents=True, exist_ok=True)

    moved = 0
    for p in legacy:
        if not p.exists():
            continue
        dest = backup / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Evita colisiones si ya existe un destino con el mismo nombre.
        if dest.exists():
            i = 1
            base = dest
            while dest.exists():
                dest = base.with_name(f"{base.name}_{i}")
                i += 1

        shutil.move(str(p), str(dest))
        moved += 1
        print(f"Movida: {p.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")

    log(f"Limpieza realizada. Carpetas movidas: {moved}. No se borra nada: queda archivado en _legacy_backup")

def sessions_template() -> None:
    ensure_dirs()
    cols = [
        "session_id", "participant_id", "date", "start_time", "duration_s", "activity", "notes",
        "edge_image_file", "cloud_raw_file", "wimu_raw_file", "spro_export_file",
        "same_interval_confirmed", "status",
    ]
    df = pd.DataFrame(columns=cols)
    out = ROOT / "data" / "sessions" / "sessions_master.xlsx"
    df.to_excel(out, index=False)
    metadata = {
        "version": VERSION,
        "unit": "session",
        "sources": ["EDGE_APP_OCR", "CLOUD_RAW_CALCULADO", "WIMU_RAW_CALCULADO", "SPRO_CALCULADO"],
        "hrv_variables": HRV_VARIABLES,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    (ROOT / "data" / "sessions" / "schema_sessions.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"Plantilla de sesiones creada: {out.relative_to(ROOT)}")



def run_edge_ocr() -> None:
    ensure_dirs()
    out, audit = process_edge_images(ROOT)
    log(f"OCR EDGE finalizado: {out.relative_to(ROOT)}")
    log(f"Auditoría OCR: {audit.relative_to(ROOT)}")


def run_sessions_scan() -> None:
    ensure_dirs()
    inventory, sessions = run_session_manager(ROOT)
    log(f"Inventario de fuentes creado: {inventory.relative_to(ROOT)}")
    log(f"Base maestra de sesiones creada: {sessions.relative_to(ROOT)}")


def run_raw_importer() -> None:
    ensure_dirs()
    audit, series = scan_and_import_raw(ROOT)
    log(f"Auditoría importación RAW: {audit.relative_to(ROOT)}")
    log(f"Series RR normalizadas: {series.relative_to(ROOT)}")

def status() -> None:
    print("=" * 90)
    print(f"EDGE2CLOUD-HRV-VALIDATOR | {VERSION}")
    print("=" * 90)
    print("Estructura oficial:")
    for rel in OFFICIAL_DIRS:
        p = ROOT / rel
        ok = "OK" if p.exists() else "FALTA"
        print(f" {ok:5s} {rel}")
    print()
    legacy = audit_legacy()
    print(f"Carpetas antiguas detectadas: {len(legacy)}")
    for p in legacy:
        print(" -", p.relative_to(ROOT))


def menu() -> None:
    while True:
        print("\n" + "=" * 90)
        print(f"EDGE2CLOUD-HRV-VALIDATOR | {VERSION}")
        print("=" * 90)
        print("1. Inicializar estructura limpia")
        print("2. Auditar carpetas antiguas")
        print("3. Limpiar carpetas antiguas a _legacy_backup")
        print("4. Crear plantilla maestra de sesiones")
        print("5. Procesar OCR imágenes EDGE/App")
        print("6. Escanear entradas y crear sesiones")
        print("7. Importar RAW CSV/Excel a RRSeries")
        print("8. Estado del proyecto")
        print("0. Salir")
        opt = input("\nSelecciona opción: ").strip()
        if opt == "1": ensure_dirs()
        elif opt == "2": print_audit()
        elif opt == "3": clean_legacy()
        elif opt == "4": sessions_template()
        elif opt == "5": run_edge_ocr()
        elif opt == "6": run_sessions_scan()
        elif opt == "7": run_raw_importer()
        elif opt == "8": status()
        elif opt == "0": break
        else: print("Opción no válida")


def main() -> None:
    parser = argparse.ArgumentParser(description="Edge2Cloud-HRV-Validator")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--audit-legacy", action="store_true")
    parser.add_argument("--clean-legacy", action="store_true")
    parser.add_argument("--sessions-template", action="store_true")
    parser.add_argument("--ocr-edge", action="store_true")
    parser.add_argument("--scan-sessions", action="store_true")
    parser.add_argument("--import-raw", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.init: ensure_dirs(); return
    if args.audit_legacy: print_audit(); return
    if args.clean_legacy: clean_legacy(); return
    if args.sessions_template: sessions_template(); return
    if args.ocr_edge: run_edge_ocr(); return
    if args.scan_sessions: run_sessions_scan(); return
    if args.import_raw: run_raw_importer(); return
    if args.status: status(); return
    menu()


if __name__ == "__main__":
    main()
