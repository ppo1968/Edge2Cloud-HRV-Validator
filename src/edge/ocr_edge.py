from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageOps, ImageFilter

HRV_VARIABLES = [
    "HR_bpm", "RMSSD_ms", "LnRMSSD", "RR_medio_ms", "SDNN_ms", "SD1_ms", "SD2_ms",
    "indice_estres", "frecuencia_respiratoria_resp_min", "LF_ms2", "HF_ms2",
    "LF_nu_pct", "HF_nu_pct", "LF_HF_ratio",
]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

ALIASES = {
    "HR_bpm": [r"\bHR\b", r"heart\s*rate", r"fc", r"frecuencia\s*card[ií]aca"],
    "RMSSD_ms": [r"RMSSD"],
    "LnRMSSD": [r"Ln\s*RMSSD", r"lnRMSSD", r"log\s*RMSSD"],
    "RR_medio_ms": [r"RR\s*(medio|mean|avg)", r"mean\s*RR", r"average\s*RR", r"RR\s*mean", r"av\s*RR"],
    "SDNN_ms": [r"SDNN"],
    "SD1_ms": [r"\bSD1\b"],
    "SD2_ms": [r"\bSD2\b"],
    "indice_estres": [r"stress\s*index", r"índice\s*estr[eé]s", r"indice\s*estres", r"SI\b"],
    "frecuencia_respiratoria_resp_min": [r"respiratory\s*rate", r"breathing\s*rate", r"frecuencia\s*respiratoria", r"resp\.?\s*rate"],
    "LF_ms2": [r"\bLF\b\s*(?:ms2|ms\^2|power)?"],
    "HF_ms2": [r"\bHF\b\s*(?:ms2|ms\^2|power)?"],
    "LF_nu_pct": [r"LF\s*(?:nu|n\.u\.|%)", r"LF\s*normalized"],
    "HF_nu_pct": [r"HF\s*(?:nu|n\.u\.|%)", r"HF\s*normalized"],
    "LF_HF_ratio": [r"LF\s*/\s*HF", r"LF\s*-\s*HF", r"LFHF", r"ratio\s*LF"],
}

NUMBER_RE = r"[-+]?\d+(?:[\.,]\d+)?"


@dataclass
class OCRResult:
    image_file: str
    status: str
    ocr_engine: str
    text_file: str
    values: dict[str, Any]
    notes: str = ""


def _import_tesseract():
    try:
        import pytesseract  # type: ignore
        return pytesseract
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "No se pudo importar pytesseract. Instala las dependencias de OCR o revisa requirements.txt."
        ) from exc


def preprocess_image(path: Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    # Aumentar tamaño mejora el OCR en capturas pequeñas.
    if img.width < 1400:
        scale = 1400 / max(img.width, 1)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def extract_text(path: Path) -> str:
    pytesseract = _import_tesseract()
    img = preprocess_image(path)
    config = "--psm 6"
    try:
        return pytesseract.image_to_string(img, lang="eng+spa", config=config)
    except Exception:
        return pytesseract.image_to_string(img, config=config)


def _clean_number(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except Exception:
        return None


def parse_values(text: str) -> dict[str, float | None]:
    values: dict[str, float | None] = {v: None for v in HRV_VARIABLES}
    normalized = re.sub(r"[\t|]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized)

    for variable, aliases in ALIASES.items():
        found: float | None = None
        for alias in aliases:
            patterns = [
                rf"(?:{alias})\s*[:=]?\s*({NUMBER_RE})",
                rf"(?:{alias}).{{0,20}}?({NUMBER_RE})",
            ]
            for pattern in patterns:
                m = re.search(pattern, normalized, flags=re.IGNORECASE)
                if m:
                    found = _clean_number(m.group(1))
                    break
            if found is not None:
                break
        values[variable] = found
    return values


def process_edge_images(root: Path) -> tuple[Path, Path]:
    input_dir = root / "data" / "input" / "edge_images"
    output_dir = root / "data" / "processed" / "edge"
    text_dir = output_dir / "ocr_text"
    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(p for p in input_dir.glob("**/*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    rows: list[dict[str, Any]] = []

    if not images:
        out = output_dir / "edge_ocr_calculado.xlsx"
        audit = output_dir / "edge_ocr_auditoria.xlsx"
        pd.DataFrame(columns=["image_file", "status", *HRV_VARIABLES]).to_excel(out, index=False)
        pd.DataFrame([{"status": "SIN_IMAGENES", "input_dir": str(input_dir.relative_to(root))}]).to_excel(audit, index=False)
        return out, audit

    for idx, img_path in enumerate(images, start=1):
        print(f"Procesando imagen EDGE {idx}/{len(images)}: {img_path.name}")
        text_file = text_dir / f"{img_path.stem}_ocr.txt"
        row: dict[str, Any] = {
            "image_file": str(img_path.relative_to(root)),
            "image_name": img_path.name,
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            text = extract_text(img_path)
            text_file.write_text(text, encoding="utf-8", errors="ignore")
            values = parse_values(text)
            n_detected = sum(v is not None for v in values.values())
            row.update(values)
            row["variables_detectadas"] = n_detected
            row["status"] = "OK" if n_detected > 0 else "OCR_SIN_VARIABLES"
            row["ocr_text_file"] = str(text_file.relative_to(root))
        except Exception as exc:
            row.update({v: None for v in HRV_VARIABLES})
            row["variables_detectadas"] = 0
            row["status"] = "ERROR_OCR"
            row["error"] = str(exc)
            row["ocr_text_file"] = ""
        rows.append(row)

    df = pd.DataFrame(rows)
    cols = ["image_file", "image_name", "status", "variables_detectadas", *HRV_VARIABLES, "ocr_text_file", "processed_at"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols + [c for c in df.columns if c not in cols]]

    out = output_dir / "edge_ocr_calculado.xlsx"
    audit = output_dir / "edge_ocr_auditoria.xlsx"
    df.to_excel(out, index=False)

    audit_df = pd.DataFrame([
        {"metric": "imagenes_detectadas", "value": len(images)},
        {"metric": "imagenes_con_variables", "value": int((df["variables_detectadas"] > 0).sum())},
        {"metric": "variables_objetivo", "value": len(HRV_VARIABLES)},
        {"metric": "input_dir", "value": str(input_dir.relative_to(root))},
        {"metric": "output_file", "value": str(out.relative_to(root))},
    ])
    audit_df.to_excel(audit, index=False)
    return out, audit
