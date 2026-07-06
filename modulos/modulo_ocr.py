# -*- coding: utf-8 -*-
"""
sportsLife7 FOTO A EXCEL - VERSION LIMPIA v02
----------------------------------------
Objetivo:
- Leer capturas/fotos de Kubios desde una carpeta.
- Extraer los datos HRV visibles mediante OCR.
- Generar UN Excel con una fila por imagen.

Uso:
1) Coloca este script en una carpeta.
2) Crea dentro una carpeta llamada: imagenes
3) Mete ahí las capturas .png/.jpg/.jpeg/.webp
4) Ejecuta: py sportsLife7_foto_a_excel_v02.py
5) Se genera: resultados/resultados_pepe/sportsLife7_pepe.xlsx

Requisitos:
    pip install opencv-python pytesseract pandas openpyxl numpy
Además, en Windows hay que tener instalado Tesseract OCR:
    https://github.com/UB-Mannheim/tesseract/wiki
"""

from pathlib import Path
import os
import re
import traceback

import cv2
import numpy as np
import pandas as pd
import pytesseract

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BASE_DIR / "imagenes"
OUTPUT_XLSX = BASE_DIR / "resultados/resultados_pepe/sportsLife7_pepe.xlsx"
IMAGE_EXTENSIONS = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp", "*.PNG", "*.JPG", "*.JPEG", "*.WEBP", "*.BMP")

# Si Tesseract está en una ruta estándar de Windows, lo detecta automáticamente.
def configurar_tesseract():
    posibles = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in posibles:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return p
    return getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")


def leer_imagen(path: Path):
    """Permite abrir imágenes aunque la ruta tenga acentos o caracteres raros."""
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def limpiar_numero(valor):
    if valor is None:
        return None
    s = str(valor).replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if s in ("", ".", "-", "-."):
        return None
    try:
        return float(s)
    except Exception:
        return None


def extraer_fecha_hora_nombre(nombre_archivo):
    """Intenta sacar fecha/hora desde el nombre del archivo, si existe."""
    stem = Path(nombre_archivo).stem
    patrones = [
        r"(?P<fecha>\d{4}-\d{2}-\d{2})[ _-]+(?P<hora>\d{2}[.:\-]\d{2}[.:\-]\d{2})",
        r"(?P<fecha>\d{2}[.\-/]\d{2}[.\-/]\d{4})[ _-]+(?P<hora>\d{2}[.:\-]\d{2}[.:\-]\d{2})",
        r"(?P<fecha>\d{4}-\d{2}-\d{2})",
        r"(?P<fecha>\d{2}[.\-/]\d{2}[.\-/]\d{4})",
    ]
    fecha, hora = None, None
    for pat in patrones:
        m = re.search(pat, stem)
        if m:
            fecha = m.groupdict().get("fecha")
            hora = m.groupdict().get("hora")
            break
    fecha_out, hora_out = None, None
    if fecha:
        fecha_out = pd.to_datetime(fecha, dayfirst=True, errors="coerce")
        fecha_out = None if pd.isna(fecha_out) else fecha_out.strftime("%Y-%m-%d")
    if hora:
        hora = hora.replace(".", ":").replace("-", ":")
        hora_out = pd.to_datetime(hora, format="%H:%M:%S", errors="coerce")
        hora_out = None if pd.isna(hora_out) else hora_out.strftime("%H:%M:%S")
    return fecha_out, hora_out


def ocr_global(img):
    """OCR principal. Funciona bien con modo oscuro de Kubios."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    big = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    txt = pytesseract.image_to_string(big, config="--psm 6")
    return txt


def buscar(texto, patrones):
    for pat in patrones:
        m = re.search(pat, texto, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return limpiar_numero(m.group(1))
    return None


def detectar_porcentaje_barras(img):
    """
    Extrae el porcentaje aproximado de relleno de las tres barras visibles:
    PNS, SNS y edad fisiológica. No son los índices reales, sino % visual de barra.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # máscaras por color: azul, naranja, morado
    masks = {
        "PNS_BARRA_PCT": cv2.inRange(hsv, np.array([90, 50, 80]), np.array([120, 255, 255])),
        "SNS_BARRA_PCT": cv2.inRange(hsv, np.array([5, 80, 120]), np.array([25, 255, 255])),
        "PHYSIO_AGE_BARRA_PCT": cv2.inRange(hsv, np.array([125, 40, 100]), np.array([165, 255, 255])),
    }

    salida = {k: None for k in masks}
    h, w = img.shape[:2]

    # Se busca solo en la mitad superior-media, donde están esas barras.
    for key, mask in masks.items():
        num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        candidatos = []
        for i in range(1, num):
            x, y, bw, bh, area = stats[i]
            if area < 500:
                continue
            if not (0.25 * h < y < 0.60 * h):
                continue
            if bw < 100 or bh < 5 or bh > 40:
                continue
            candidatos.append((x, y, bw, bh, area))
        if candidatos:
            x, y, bw, bh, area = max(candidatos, key=lambda t: t[2] * t[4])
            # En la captura típica la barra completa ocupa aproximadamente de x=75 a x=755.
            # Para hacerlo adaptable, estimamos ancho total como el ancho útil de la pantalla menos márgenes.
            ancho_total_estimado = max(1, int(w * 0.84))
            salida[key] = round(min(100.0, max(0.0, 100.0 * bw / ancho_total_estimado)), 1)
    return salida


def extraer_datos(path: Path):
    img = leer_imagen(path)
    if img is None:
        raise ValueError(f"No se pudo abrir la imagen: {path.name}")

    texto = ocr_global(img)
    fecha, hora = extraer_fecha_hora_nombre(path.name)

    datos = {
        "archivo": path.name,
        "fecha_archivo": fecha,
        "hora_archivo": hora,
        "HR_bpm": buscar(texto, [
            r"Heart\s*rate\s*([0-9]+(?:[.,][0-9]+)?)\s*bpm",
            r"Frecuencia\s*cardiaca\s*([0-9]+(?:[.,][0-9]+)?)",
            r"FC\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "RMSSD_ms": buscar(texto, [
            r"RMSSD\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"RMSSD\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "RR_medio_ms": buscar(texto, [
            r"RR\s*Medio\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"Mean\s*RR\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"RR\s*mean\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "SDNN_ms": buscar(texto, [
            r"SDNN\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"\bSDNN\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "SD1_ms": buscar(texto, [
            r"Poincar[ée]\s*SD1\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"SD1\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
        ]),
        "SD2_ms": buscar(texto, [
            r"Poincar[ée]\s*SD2\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"SD2\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
        ]),
        "indice_estres": buscar(texto, [
            r"[ÍI]ndice\s*de\s*Estr[eé]s\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Stress\s*index\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "frecuencia_respiratoria_resp_min": buscar(texto, [
            r"Frec\.?,?\s*Resp\.?,?\s*Est\.?,?\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Respiratory\s*rate\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Resp\.?.*?([0-9]+(?:[.,][0-9]+)?)\s*resp",
        ]),
        "LF_ms2": buscar(texto, [
            r"Potencia\s*LF\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"LF\s*power\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
        ]),
        "HF_ms2": buscar(texto, [
            r"Potencia\s*HF\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
            r"HF\s*power\s*([0-9]+(?:[.,][0-9]+)?)\s*ms",
        ]),
        "LF_nu_pct": buscar(texto, [
            r"Potencia\s*LF\s*\(n\.u\.\)\s*([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"LF\s*power\s*\(n\.u\.\)\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "HF_nu_pct": buscar(texto, [
            r"Potencia\s*HF\s*\(n\.u\.\)\s*([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"HF\s*power\s*\(n\.u\.\)\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
        "LF_HF_ratio": buscar(texto, [
            r"LF\/HF\s*ratio\s*([0-9]+(?:[.,][0-9]+)?)",
            r"LF\/HF\s*([0-9]+(?:[.,][0-9]+)?)",
        ]),
    }

    # Transformación útil para análisis longitudinal.
    if datos["RMSSD_ms"] and datos["RMSSD_ms"] > 0:
        datos["LnRMSSD"] = round(float(np.log(datos["RMSSD_ms"])), 4)
    else:
        datos["LnRMSSD"] = None

    datos.update(detectar_porcentaje_barras(img))
    datos["OCR_texto"] = texto

    # Estado simple de calidad de extracción.
    claves_principales = ["HR_bpm", "RMSSD_ms", "RR_medio_ms", "SDNN_ms", "SD1_ms", "SD2_ms"]
    n_ok = sum(datos.get(k) is not None for k in claves_principales)
    datos["estado_extraccion"] = "OK" if n_ok >= 5 else "REVISAR"
    datos["variables_principales_detectadas"] = n_ok
    return datos



def ajustar_excel(path_xlsx):
    from openpyxl import load_workbook
    wb = load_workbook(path_xlsx)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            letra = col[0].column_letter
            max_len = 0
            for cell in col:
                txt = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, min(len(txt), 60))
            ws.column_dimensions[letra].width = max(10, max_len + 2)
    wb.save(path_xlsx)


def carpeta_tiene_imagenes(carpeta: Path) -> bool:
    for ext in IMAGE_EXTENSIONS:
        if list(carpeta.glob(ext)):
            return True
    return False


def imagenes_de_carpeta(carpeta: Path):
    archivos = []
    for ext in IMAGE_EXTENSIONS:
        archivos.extend(sorted(carpeta.glob(ext)))
    return sorted(set(archivos), key=lambda x: x.name.lower())


def nombre_persona_desde_carpeta(carpeta: Path) -> str:
    nombre = carpeta.name.strip()
    if nombre.lower().startswith("imagenes_"):
        nombre = nombre[len("imagenes_"):]
    nombre = re.sub(r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ_-]+", "_", nombre).strip("_")
    return nombre if nombre else "sin_nombre"


def detectar_carpetas_imagenes():
    """Devuelve carpetas de personas dentro de /imagenes y, si hay imágenes sueltas, la raíz."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    carpetas = []

    # Imágenes sueltas directamente dentro de imagenes
    if carpeta_tiene_imagenes(IMAGES_DIR):
        carpetas.append(("general", IMAGES_DIR))

    # Subcarpetas tipo imagenes_pepe, imagenes_maria, etc.
    for sub in sorted([x for x in IMAGES_DIR.iterdir() if x.is_dir()], key=lambda x: x.name.lower()):
        if carpeta_tiene_imagenes(sub):
            carpetas.append((nombre_persona_desde_carpeta(sub), sub))

    return carpetas


def seleccionar_carpetas(carpetas):
    print("\nCarpetas detectadas dentro de 'imagenes':")
    for i, (persona, carpeta) in enumerate(carpetas, start=1):
        print(f"{i}. {persona}  ->  {carpeta}")
    print("0. Todas")
    print("\nPuedes elegir una o varias: 1   o   1,3,4   o   0")

    while True:
        entrada = input("Selecciona carpeta(s): ").strip().lower()
        if entrada in {"0", "todas", "todo"}:
            return carpetas, True
        partes = [x.strip() for x in entrada.split(",") if x.strip()]
        if not partes or not all(x.isdigit() for x in partes):
            print("Entrada no válida. Ejemplo: 1,2 o 0 para todas.")
            continue
        indices = sorted(set(int(x) for x in partes))
        if any(i < 1 or i > len(carpetas) for i in indices):
            print("Hay números fuera del listado.")
            continue
        return [carpetas[i - 1] for i in indices], len(indices) == len(carpetas)



def leer_excel_existente(path_xlsx: Path) -> pd.DataFrame:
    """Lee la hoja datos de un Excel existente. Si no existe, devuelve DataFrame vacío."""
    if not path_xlsx.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path_xlsx, sheet_name="datos")
    except Exception:
        return pd.DataFrame()


def claves_archivos_procesados(df_existente: pd.DataFrame) -> set:
    """Usa el nombre del archivo como clave principal para no repetir imágenes."""
    if df_existente is None or df_existente.empty or "archivo" not in df_existente.columns:
        return set()
    return set(df_existente["archivo"].dropna().astype(str).tolist())


def procesar_carpeta(persona: str, carpeta: Path, xlsx_persona: Path):
    archivos = imagenes_de_carpeta(carpeta)
    df_existente = leer_excel_existente(xlsx_persona)
    ya_procesados = claves_archivos_procesados(df_existente)
    archivos_nuevos = [p for p in archivos if p.name not in ya_procesados]

    filas, errores = [], []

    print(f"\n--- Analizando {persona} ---")
    print(f"Imágenes en carpeta: {len(archivos)}")
    print(f"Ya estaban en Excel: {len(ya_procesados)}")
    print(f"Nuevas por procesar: {len(archivos_nuevos)}")

    if not archivos_nuevos:
        return df_existente, pd.DataFrame(), 0

    for i, img_path in enumerate(archivos_nuevos, start=1):
        print(f"[{i}/{len(archivos_nuevos)}] {img_path.name}")
        try:
            fila = extraer_datos(img_path)
            fila["persona"] = persona
            fila["carpeta_origen"] = str(carpeta)
            fila["fecha_procesado"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            filas.append(fila)
        except Exception as e:
            errores.append({"persona": persona, "archivo": img_path.name, "carpeta_origen": str(carpeta), "error": str(e), "fecha_error": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")})

    df_nuevo = pd.DataFrame(filas)
    if not df_existente.empty and not df_nuevo.empty:
        df_acumulado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_acumulado = df_acumulado.drop_duplicates(subset=["archivo"], keep="last")
    elif not df_existente.empty:
        df_acumulado = df_existente.copy()
    else:
        df_acumulado = df_nuevo.copy()

    return df_acumulado, pd.DataFrame(errores), len(df_nuevo)


def ordenar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    columnas_primero = [
        "persona", "archivo", "carpeta_origen", "fecha_procesado", "fecha_archivo", "hora_archivo", "estado_extraccion", "variables_principales_detectadas",
        "HR_bpm", "RMSSD_ms", "LnRMSSD", "RR_medio_ms", "SDNN_ms", "SD1_ms", "SD2_ms",
        "indice_estres", "frecuencia_respiratoria_resp_min", "LF_ms2", "HF_ms2", "LF_nu_pct", "HF_nu_pct", "LF_HF_ratio",
        "PNS_BARRA_PCT", "SNS_BARRA_PCT", "PHYSIO_AGE_BARRA_PCT",
    ]
    if df.empty:
        return df
    columnas = [c for c in columnas_primero if c in df.columns] + [c for c in df.columns if c not in columnas_primero]
    return df[columnas]


def guardar_excel(df: pd.DataFrame, errores: pd.DataFrame, salida_xlsx: Path, incluir_ocr=True, nuevas=0):
    salida_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df = ordenar_columnas(df.copy()) if df is not None else pd.DataFrame()

    resumen = pd.DataFrame([{
        "imagenes_en_excel_acumulado": len(df),
        "imagenes_nuevas_esta_ejecucion": int(nuevas),
        "imagenes_con_error_esta_ejecucion": len(errores),
        "registros_OK": int((df["estado_extraccion"] == "OK").sum()) if not df.empty and "estado_extraccion" in df.columns else 0,
        "registros_REVISAR": int((df["estado_extraccion"] == "REVISAR").sum()) if not df.empty and "estado_extraccion" in df.columns else 0,
        "personas": ", ".join(sorted(df["persona"].dropna().astype(str).unique())) if not df.empty and "persona" in df.columns else "",
        "ultima_actualizacion": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    with pd.ExcelWriter(salida_xlsx, engine="openpyxl") as writer:
        df.drop(columns=["OCR_texto"], errors="ignore").to_excel(writer, sheet_name="datos", index=False)
        resumen.to_excel(writer, sheet_name="resumen", index=False)
        if incluir_ocr and "OCR_texto" in df.columns:
            cols_ocr = [c for c in ["persona", "archivo", "OCR_texto"] if c in df.columns]
            df[cols_ocr].to_excel(writer, sheet_name="ocr_texto", index=False)
        if errores is not None and not errores.empty:
            errores.to_excel(writer, sheet_name="errores_ultima_ejecucion", index=False)

    ajustar_excel(salida_xlsx)


def generar_excel_global_desde_individuales(resultados_dir: Path):
    """Reconstruye el Excel global acumulativo leyendo todos los Excel individuales existentes."""
    dfs = []
    for xlsx in sorted(resultados_dir.glob("resultados_*/sportsLife7_*.xlsx")):
        if xlsx.parent.name == "resultados_todas":
            continue
        df = leer_excel_existente(xlsx)
        if not df.empty:
            dfs.append(df)
    if not dfs:
        return None, 0
    df_total = pd.concat(dfs, ignore_index=True)
    if "archivo" in df_total.columns and "persona" in df_total.columns:
        df_total = df_total.drop_duplicates(subset=["persona", "archivo"], keep="last")
    salida = resultados_dir / "resultados_todas" / "sportsLife7_todas.xlsx"
    guardar_excel(df_total, pd.DataFrame(), salida, incluir_ocr=True, nuevas=0)
    return salida, len(df_total)


def ejecutar_ocr():
    print("========================================")
    print("sportsLife7 - FOTO A EXCEL v03 ACUMULATIVO")
    print("========================================")
    print(f"Carpeta del script: {BASE_DIR}")
    print(f"Carpeta principal de imágenes: {IMAGES_DIR}")
    print(f"Carpeta principal de resultados: {BASE_DIR / 'resultados'}")
    print("")

    configurar_tesseract()

    if not IMAGES_DIR.exists():
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        print("He creado la carpeta 'imagenes'.")
        print("Dentro puedes poner imágenes sueltas o carpetas como: imagenes_pepe, imagenes_maria, etc.")
        return

    carpetas = detectar_carpetas_imagenes()
    if not carpetas:
        print("No hay imágenes para analizar.")
        print("Pon las capturas dentro de 'imagenes' o dentro de subcarpetas como 'imagenes_pepe'.")
        return

    seleccionadas, es_todas = seleccionar_carpetas(carpetas)

    resultados_dir = BASE_DIR / "resultados"
    resultados_dir.mkdir(parents=True, exist_ok=True)

    total_nuevas = 0
    total_errores = 0

    for persona, carpeta in seleccionadas:
        carpeta_resultado_persona = resultados_dir / f"resultados_{persona}"
        xlsx_persona = carpeta_resultado_persona / f"sportsLife7_{persona}.xlsx"

        df_acumulado, err_persona, n_nuevas = procesar_carpeta(persona, carpeta, xlsx_persona)
        guardar_excel(df_acumulado, err_persona, xlsx_persona, incluir_ocr=True, nuevas=n_nuevas)

        total_nuevas += n_nuevas
        total_errores += len(err_persona)
        print(f"Excel acumulativo individual: {xlsx_persona}")

    # El Excel global se reconstruye a partir de todos los Excel individuales existentes.
    # Así siempre es acumulativo aunque hoy solo analices una persona.
    salida_global, n_total = generar_excel_global_desde_individuales(resultados_dir)
    if salida_global:
        print(f"\nExcel global acumulativo actualizado: {salida_global}")
        print(f"Registros totales en global: {n_total}")

    print("\nProceso terminado correctamente.")
    print(f"Nuevas imágenes procesadas esta vez: {total_nuevas}")
    print(f"Errores esta vez: {total_errores}")


# Compatibilidad si se ejecuta directamente
def main():
    ejecutar_ocr()

if __name__ == "__main__":
    try:
        ejecutar_ocr()
    except Exception:
        print("ERROR DURANTE LA EJECUCIÓN")
        print(traceback.format_exc())
        input("Pulsa Enter para salir...")
