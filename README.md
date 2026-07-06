# Edge2Cloud-HRV-Validator

<div align="center">

## Open-Source Framework for Validating Heart Rate Variability (HRV) Processing Between Edge and Cloud

**Version:** 0.1 (Development)

</div>

---

# Overview

Edge2Cloud-HRV-Validator is an open-source scientific framework designed to evaluate the agreement between Heart Rate Variability (HRV) metrics calculated directly on Edge devices and the same metrics recalculated from raw RR interval data in the Cloud.

The framework has been developed to provide an automated, transparent and reproducible quality-control process for HRV applications.

---

# Main Features

- Automatic OCR extraction from HRV screenshots.
- Automatic processing of RR interval files.
- Edge vs Cloud comparison.
- Quality-control assessment.
- Automatic Excel reports.
- Automatic scientific reports.
- Batch processing of multiple subjects.
- Reproducible workflow.

---

# Workflow

```
Edge Device
      │
      ▼
 Screenshot (PNG/JPG)
      │
      ▼
 OCR Extraction
      │
      ▼
 Edge Results
      │
      ▼
 Comparison
      ▲
      │
 Raw RR intervals
      │
      ▼
 Cloud Recalculation
```

---

# Current Modules

| Module | Status |
|---------|--------|
| OCR extraction | ✅ |
| Automatic Excel | ✅ |
| Folder management | ✅ |
| RAW processing | 🚧 |
| Edge vs Cloud comparison | 🚧 |
| Dashboard | 🚧 |
| Scientific report | 🚧 |

---

# Folder Structure

```
Edge2Cloud-HRV-Validator
│
├── main.py
├── modulos
├── demo
├── docs
├── resultados
├── imagenes
└── raw
```

---

# Future Development

- Bland–Altman analysis
- ICC calculation
- RMSE
- Bias
- Dashboard
- Automatic validation reports
- Scientific quality indicators

---

# Authors

José Pino-Ortega

Faculty of Sport Sciences

University of Murcia

Spain

---

# License

MIT License

---

# Citation

If you use this software in your research, please cite the corresponding publication (coming soon).

---

# Project Status

🚧 Under active development.