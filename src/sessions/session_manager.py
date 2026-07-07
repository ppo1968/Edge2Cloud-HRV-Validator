from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

INPUT_SOURCES = {
    "EDGE": "edge_images",
    "CLOUD": "cloud_raw",
    "WIMU": "wimu_raw",
    "SPRO": "spro_export",
}

EDGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DATA_EXT = {".xlsx", ".xls", ".csv", ".txt", ".json"}


@dataclass
class SourceFile:
    source: str
    filename: str
    relative_path: str
    suffix: str
    size_bytes: int
    modified_time: str
    proposed_date: str
    proposed_time: str
    match_key: str


def _sha_short(text: str, n: int = 8) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:n]


def _extract_date_time(name: str) -> tuple[str, str]:
    """Extrae fecha y hora de nombres frecuentes sin imponer un fabricante.

    Soporta patrones como:
    - 20260626
    - 2026-06-26 / 2026_06_26
    - UTC140410 / 140410
    """
    base = name.replace("-", "_").replace(".", "_")

    date = ""
    m = re.search(r"(20\d{2})[_]?(\d{2})[_]?(\d{2})", base)
    if m:
        y, mo, d = m.groups()
        date = f"{y}-{mo}-{d}"

    time = ""
    mt = re.search(r"(?:UTC)?([01]\d|2[0-3])([0-5]\d)([0-5]\d)", base, flags=re.IGNORECASE)
    if mt:
        hh, mm, ss = mt.groups()
        time = f"{hh}:{mm}:{ss}"

    return date, time


def _match_key(source: str, filename: str) -> str:
    date, time = _extract_date_time(filename)
    if date:
        # Si hay fecha, usamos fecha + hora redondeada a minuto si existe.
        if time:
            return f"{date}_{time[:5].replace(':', '')}"
        return date

    # Fallback estable: nombre limpio. No agrupa agresivamente para evitar falsos emparejamientos.
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"{source.lower()}_{stem[:50]}_{_sha_short(filename)}"


def scan_input_sources(root: Path) -> pd.DataFrame:
    rows: list[dict] = []
    input_root = root / "data" / "input"

    for source, folder in INPUT_SOURCES.items():
        folder_path = input_root / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        allowed = EDGE_EXT if source == "EDGE" else DATA_EXT
        for file in sorted(folder_path.rglob("*")):
            if not file.is_file() or file.name.startswith("."):
                continue
            if file.suffix.lower() not in allowed:
                continue
            stat = file.stat()
            date, time = _extract_date_time(file.name)
            item = SourceFile(
                source=source,
                filename=file.name,
                relative_path=str(file.relative_to(root)),
                suffix=file.suffix.lower(),
                size_bytes=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                proposed_date=date,
                proposed_time=time,
                match_key=_match_key(source, file.name),
            )
            rows.append(asdict(item))

    cols = [
        "source", "filename", "relative_path", "suffix", "size_bytes", "modified_time",
        "proposed_date", "proposed_time", "match_key",
    ]
    return pd.DataFrame(rows, columns=cols)


def build_sessions_from_inventory(inventory: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "session_id", "match_key", "participant_id", "date", "start_time", "duration_s", "activity",
        "edge_image_file", "cloud_raw_file", "wimu_raw_file", "spro_export_file",
        "same_interval_confirmed", "status", "notes",
    ]
    if inventory.empty:
        return pd.DataFrame(columns=cols)

    rows: list[dict] = []
    grouped = inventory.groupby("match_key", dropna=False, sort=True)
    for i, (key, g) in enumerate(grouped, start=1):
        def first_path(src: str) -> str:
            s = g[g["source"] == src]
            return "" if s.empty else str(s.iloc[0]["relative_path"])

        n_sources = int(g["source"].nunique())
        status = "completa" if n_sources == 4 else "parcial"
        first = g.iloc[0]
        rows.append({
            "session_id": f"S{i:04d}",
            "match_key": key,
            "participant_id": "",
            "date": first.get("proposed_date", ""),
            "start_time": first.get("proposed_time", ""),
            "duration_s": "",
            "activity": "",
            "edge_image_file": first_path("EDGE"),
            "cloud_raw_file": first_path("CLOUD"),
            "wimu_raw_file": first_path("WIMU"),
            "spro_export_file": first_path("SPRO"),
            "same_interval_confirmed": "NO",
            "status": status,
            "notes": "revisar emparejamiento automático" if status == "parcial" else "",
        })
    return pd.DataFrame(rows, columns=cols)


def create_session_folders(root: Path, sessions: pd.DataFrame) -> None:
    sessions_root = root / "data" / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    for _, row in sessions.iterrows():
        sid = str(row["session_id"])
        sdir = sessions_root / sid
        for sub in ["edge", "cloud", "wimu", "spro", "processed", "comparison"]:
            (sdir / sub).mkdir(parents=True, exist_ok=True)
        manifest = {
            "session_id": sid,
            "match_key": row.get("match_key", ""),
            "participant_id": row.get("participant_id", ""),
            "date": row.get("date", ""),
            "start_time": row.get("start_time", ""),
            "same_interval_confirmed": row.get("same_interval_confirmed", "NO"),
            "files": {
                "edge_image_file": row.get("edge_image_file", ""),
                "cloud_raw_file": row.get("cloud_raw_file", ""),
                "wimu_raw_file": row.get("wimu_raw_file", ""),
                "spro_export_file": row.get("spro_export_file", ""),
            },
            "status": row.get("status", ""),
        }
        (sdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def run_session_manager(root: Path) -> tuple[Path, Path]:
    out_dir = root / "data" / "sessions"
    out_dir.mkdir(parents=True, exist_ok=True)

    inventory = scan_input_sources(root)
    inventory_path = out_dir / "inventory_sources.xlsx"
    inventory.to_excel(inventory_path, index=False)

    sessions = build_sessions_from_inventory(inventory)
    sessions_path = out_dir / "sessions_master.xlsx"
    sessions.to_excel(sessions_path, index=False)

    create_session_folders(root, sessions)
    return inventory_path, sessions_path
