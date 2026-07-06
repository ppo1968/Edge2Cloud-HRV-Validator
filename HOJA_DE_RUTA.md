\# HOJA DE RUTA - Edge2Cloud-HRV-Validator



\## Objetivo general

Validar la información mostrada por Garmin Edge a partir de archivos RAW y fotografías de pantalla, comparando datos originales, OCR y resultados calculados.



\## v0.1.0 - Estructura inicial funcional

\- \[x] Crear repositorio GitHub

\- \[x] Crear estructura básica del proyecto

\- \[x] Revisar main.py

\- \[x] Revisar modulo\_raw.py

\- \[x] Ejecutar primera prueba local



\## v0.2.0 - Lectura de datos RAW

\- \[ ] Detectar archivos en raw/

\- \[ ] Leer CSV/FIT si existen

\- \[ ] Extraer frecuencia cardiaca

\- \[ ] Extraer RR si está disponible

\- \[ ] Generar resumen en pantalla



\## v0.3.0 - OCR de imágenes Garmin

\- \[ ] Detectar imágenes en imagenes/

\- \[ ] Aplicar OCR

\- \[ ] Extraer variables visibles

\- \[ ] Guardar resultados OCR



\## v0.4.0 - Comparación RAW vs OCR

\- \[ ] Unir datos RAW y OCR

\- \[ ] Calcular diferencias

\- \[ ] Calcular error absoluto

\- \[ ] Calcular error relativo



\## v0.5.0 - Informes

\- \[ ] Generar Excel

\- \[ ] Generar Word

\- \[ ] Guardar figuras

