from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd

from .rr_series import RRSeries

RR_ALIASES = [
    "rr", "rr_ms", "rr interval", "rr_interval", "r-r", "r r", "rri", "ibi", "ibi_ms",
    "interval", "interval_ms", "heart period", "heart_period", "nn", "nn_ms",
]
TIME_ALIASES = ["time", "timestamp", "elapsed", "seconds", "second", "segundos", "tiempo", "time_s", "t"]
SUPPORTED = {".csv", ".txt", ".tsv", ".xlsx", ".xls"}


def _norm(text: object) -> str:
    s = str(text).strip().lower()
    s = re.sub(r"[\n\r\t]+", " ", s)
    s = s.replace("(ms)", " ms").replace("[ms]", " ms")
    s = re.sub(r"[^a-z0-9áéíóúüñ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _score_rr_col(col: str) -> int:
    n = _norm(col)
    score = 0
    for alias in RR_ALIASES:
        a = _norm(alias)
        if n == a:
            score += 100
        elif a in n:
            score += 50
    if "ms" in n:
        score += 10
    if "hr" in n or "bpm" in n or "heart rate" in n:
        score -= 40
    return score


def _score_time_col(col: str) -> int:
    n = _norm(col)
    score = 0
    for alias in TIME_ALIASES:
        a = _norm(alias)
        if n == a:
            score += 100
        elif a in n:
            score += 50
    if "rr" in n or "ibi" in n:
        score -= 50
    return score


def _read_csv(path: Path) -> pd.DataFrame:
    # sep=None usa el detector de pandas para coma, punto y coma, tabulador, etc.
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        for sep in [";", ",", "\t", "|"]:
            try:
                return pd.read_csv(path, sep=sep)
            except Exception:
                continue
        raise


def _candidate_frames(path: Path) -> list[tuple[Optional[str], pd.DataFrame]]:
    ext = path.suffix.lower()
    if ext in {".csv", ".txt", ".tsv"}:
        return [(None, _read_csv(path))]
    if ext in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        return [(name, df) for name, df in sheets.items()]
    raise ValueError(f"Formato no soportado: {path.suffix}")


def _to_numeric_series(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _detect_columns(df: pd.DataFrame) -> tuple[Optional[str], Optional[str], str]:
    rr_scores = {col: _score_rr_col(str(col)) for col in df.columns}
    rr_col = max(rr_scores, key=rr_scores.get) if rr_scores else None
    if rr_col is not None and rr_scores[rr_col] <= 0:
        # Fallback: columna numérica con valores plausibles de RR.
        best_col = None
        best_count = -1
        for col in df.columns:
            x = _to_numeric_series(df[col])
            count = int(((x > 0.25) & (x < 2.5)).sum() + ((x > 250) & (x < 2500)).sum())
            if count > best_count:
                best_col, best_count = col, count
        rr_col = best_col if best_count > 10 else None

    time_scores = {col: _score_time_col(str(col)) for col in df.columns if col != rr_col}
    time_col = max(time_scores, key=time_scores.get) if time_scores else None
    if time_col is not None and time_scores[time_col] <= 0:
        time_col = None

    note = f"rr_scores={rr_scores}"
    return rr_col, time_col, note


def _normalise_rr(rr: pd.Series) -> tuple[list[float], str, str]:
    x = _to_numeric_series(rr).dropna()
    x = x[x > 0]
    if x.empty:
        return [], "unknown", "sin valores RR numéricos"

    median = float(x.median())
    if median < 10:
        # Probablemente segundos.
        x = x * 1000.0
        unit = "s_to_ms"
    else:
        unit = "ms"
    # Rango fisiológico amplio, no limpieza HRV todavía.
    x = x[(x >= 250) & (x <= 2500)]
    return [float(v) for v in x.tolist()], unit, ""


def _normalise_time(time: Optional[pd.Series], n: int, rr_ms: list[float]) -> Optional[list[float]]:
    if time is not None:
        t = _to_numeric_series(time).dropna()
        if len(t) >= n:
            t = t.iloc[:n]
            # Si parece milisegundos, convertir a segundos.
            if float(t.max()) > 10000:
                t = t / 1000.0
            return [float(v) for v in t.tolist()]
    # Si no hay tiempo, lo reconstruimos por suma acumulada de RR.
    if rr_ms:
        acc = []
        total = 0.0
        for v in rr_ms:
            total += v / 1000.0
            acc.append(total)
        return acc
    return None


def infer_source(path: Path) -> str:
    p = str(path).lower()
    if "cloud" in p:
        return "cloud"
    if "wimu" in p:
        return "wimu"
    return "raw"


def import_rr_file(path: str | Path, session_id: Optional[str] = None, source: Optional[str] = None) -> RRSeries:
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Formato no soportado: {path.suffix}")
    session_id = session_id or path.stem
    source = source or infer_source(path)

    best = None
    best_n = -1
    errors = []
    for sheet, df in _candidate_frames(path):
        if df.empty:
            continue
        df = df.dropna(axis=1, how="all")
        rr_col, time_col, note = _detect_columns(df)
        if rr_col is None:
            errors.append(f"{sheet or 'csv'}: no se detecta columna RR")
            continue
        rr_ms, unit, unit_note = _normalise_rr(df[rr_col])
        if len(rr_ms) > best_n:
            time_s = _normalise_time(df[time_col] if time_col else None, len(rr_ms), rr_ms)
            best = (sheet, rr_col, time_col, rr_ms, time_s, unit, note, unit_note)
            best_n = len(rr_ms)

    if best is None:
        return RRSeries(
            session_id=session_id, source=source, file_name=path.name, sheet_name=None,
            rr_ms=[], status="no_rr_detectado", notes="; ".join(errors)
        )

    sheet, rr_col, time_col, rr_ms, time_s, unit, note, unit_note = best
    n = len(rr_ms)
    duration = (sum(rr_ms) / 1000.0) if rr_ms else None
    status = "valido" if n >= 120 and duration and duration >= 120 else "insuficiente"
    notes = "; ".join([x for x in [note, unit_note] if x])
    return RRSeries(
        session_id=session_id, source=source, file_name=path.name, sheet_name=sheet,
        rr_ms=rr_ms, time_s=time_s, detected_rr_column=str(rr_col),
        detected_time_column=str(time_col) if time_col else None,
        rr_unit=unit, n_intervals=n, duration_s=duration,
        rr_min_ms=min(rr_ms) if rr_ms else None, rr_max_ms=max(rr_ms) if rr_ms else None,
        rr_mean_ms=(sum(rr_ms) / n) if n else None, status=status, notes=notes
    )


def scan_and_import_raw(root: Path) -> tuple[Path, Path]:
    input_dirs = [root / "data" / "input" / "cloud_raw", root / "data" / "input" / "wimu_raw"]
    out_dir = root / "data" / "processed" / "raw_imports"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    series_frames = []
    for folder in input_dirs:
        source = "cloud" if folder.name == "cloud_raw" else "wimu"
        for path in sorted(folder.glob("**/*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                continue
            session_id = path.stem
            serie = import_rr_file(path, session_id=session_id, source=source)
            serie.save(out_dir)
            rows.append(serie.metadata())
            if serie.rr_ms:
                series_frames.append(serie.to_frame())

    audit = pd.DataFrame(rows)
    audit_path = out_dir / "raw_import_audit.xlsx"
    audit.to_excel(audit_path, index=False)

    all_path = out_dir / "rr_series_normalizadas.xlsx"
    if series_frames:
        pd.concat(series_frames, ignore_index=True).to_excel(all_path, index=False)
    else:
        pd.DataFrame(columns=["session_id", "source", "time_s", "rr_ms"]).to_excel(all_path, index=False)
    return audit_path, all_path
