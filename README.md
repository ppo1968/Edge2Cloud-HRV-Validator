# Edge2Cloud-HRV-Validator v0.4.4

Versión centrada en el **Importador Universal RAW**.

## Estructura de entrada

Coloca los archivos CSV o Excel en:

```text
data/input/cloud_raw
data/input/wimu_raw
```

Formatos admitidos:

```text
.csv
.txt
.tsv
.xlsx
.xls
```

## Uso

Modo menú:

```bash
python main.py
```

Opción:

```text
7. Importar RAW CSV/Excel a RRSeries
```

Modo directo:

```bash
python main.py --import-raw
```

## Salidas

```text
data/processed/raw_imports/raw_import_audit.xlsx
data/processed/raw_imports/rr_series_normalizadas.xlsx
data/processed/raw_imports/*_rr_normalizado.csv
data/processed/raw_imports/*_rr_metadata.json
```

## Qué hace

- Lee CSV, TXT, TSV, XLSX y XLS.
- Detecta separadores de CSV automáticamente.
- Revisa todas las hojas de Excel.
- Detecta columnas RR/IBI/NN/intervalos.
- Convierte segundos a milisegundos cuando procede.
- Genera una serie interna normalizada `RRSeries`.
- No calcula HRV todavía.

## Regla científica

El motor HRV solo trabajará sobre `RRSeries`. Así se usará el mismo algoritmo para Cloud RAW y WIMU RAW.
