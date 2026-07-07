# Edge2Cloud-HRV-Validator

**Edge2Cloud-HRV-Validator** is a scientific software project for comparing heart rate variability (HRV) metrics obtained from edge-based systems and cloud-based processing workflows.

The project is designed for applied research in sports science, exercise monitoring and physiological signal validation.

## Purpose

The main objective is to validate and compare HRV variables obtained from different processing environments:

- Edge processing.
- Cloud processing.
- Reference systems.
- WIMU / SPRO-derived data when available.
- Standardized HRV metrics.

## Main variables

The project focuses on variables such as:

- HR_bpm
- RMSSD_ms
- LnRMSSD
- RR_medio_ms
- SDNN_ms
- SD1_ms
- SD2_ms
- indice_estres
- frecuencia_respiratoria_resp_min
- LF_ms2
- HF_ms2
- LF_nu_pct
- HF_nu_pct
- LF_HF_ratio

## Repository structure

```text
Edge2Cloud-HRV-Validator/
│
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
│
├── modules/
├── assets/
├── docs/
├── ejemplos/
├── presentaciones/
├── publicaciones/
├── videos/
├── legacy/
└── .github/
```

## Local folders not uploaded to GitHub

The following folders are intended for local work and should not be uploaded to GitHub:

```text
Datos/
Resultados/
```

They may contain raw data, generated reports, images, Excel files or sensitive project outputs.

## Scientific use

This repository is intended to evolve as a living scientific software project, including:

- Source code.
- Manuals.
- Examples.
- Practical cases.
- Changelog.
- Roadmap.
- FAQ.
- Documentation.
- Presentations.
- Links to videos.
- Future scientific publications.
