# -*- coding: utf-8 -*-
"""
Comparación EDGE vs CLOUD.
Cruce previsto: F001 <-> R001 por el número del código.
"""
from pathlib import Path
import re
import pandas as pd
import numpy as np

VARIABLES = ['HR_bpm','RMSSD_ms','LnRMSSD','RR_medio_ms','SDNN_ms','SD1_ms','SD2_ms']


def id_desde_codigo(nombre):
    m = re.search(r'[FR](\d+)', str(nombre), flags=re.I)
    return m.group(1).zfill(3) if m else None


def comparar_edge_cloud(base_dir: Path):
    resultados = base_dir / 'resultados'
    edge_files = list(resultados.glob('resultados_todas/sportsLife7_todas.xlsx')) + list(resultados.glob('resultados_*/sportsLife7_*.xlsx'))
    cloud_files = list((resultados / 'cloud').glob('*.xlsx'))
    if not edge_files:
        print('No encuentro Excel EDGE. Ejecuta primero la opción 1.')
        return None
    if not cloud_files:
        print('No encuentro Excel CLOUD. Ejecuta primero la opción 2 cuando el módulo RAW esté completado.')
        return None
    print('Comparación pendiente: falta definir formato definitivo del CLOUD calculado desde RAW.')
    return None
