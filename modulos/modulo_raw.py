# -*- coding: utf-8 -*-
"""
Módulo RAW/CLOUD - pendiente de completar cuando tengamos el formato real del raw.
Entrada prevista: raw/R001.xlsx, raw/R002.csv, etc.
Salida prevista: resultados/cloud/sportsLife7_cloud.xlsx
"""
from pathlib import Path
import pandas as pd


def procesar_raw(base_dir: Path):
    raw_dir = base_dir / 'raw'
    out_dir = base_dir / 'resultados' / 'cloud'
    out_dir.mkdir(parents=True, exist_ok=True)
    archivos = []
    for ext in ('*.xlsx','*.xls','*.csv','*.txt'):
        archivos.extend(raw_dir.glob(ext))
    if not archivos:
        print('No hay archivos RAW en la carpeta raw/.')
        return None
    # Plantilla mínima hasta definir columnas reales del RAW.
    df = pd.DataFrame({'archivo_raw':[p.name for p in archivos], 'estado':['PENDIENTE_DE_CALCULO']*len(archivos)})
    salida = out_dir / 'sportsLife7_cloud_pendiente.xlsx'
    df.to_excel(salida, index=False)
    print(f'Plantilla CLOUD generada: {salida}')
    return salida
