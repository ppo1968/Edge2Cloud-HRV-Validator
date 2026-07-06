# -*- coding: utf-8 -*-
from pathlib import Path
import traceback

from modulos.modulo_ocr import ejecutar_ocr
from modulos.modulo_raw import procesar_raw
from modulos.modulo_comparacion import comparar_edge_cloud
from modulos.utils import abrir_carpeta, pausa

BASE_DIR = Path(__file__).resolve().parent
VERSION = "0.2.0"


def asegurar_estructura():
    for carpeta in ["imagenes", "raw", "resultados", "modulos", "docs"]:
        (BASE_DIR / carpeta).mkdir(parents=True, exist_ok=True)


def contar_imagenes():
    exts = ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp",
            "*.PNG", "*.JPG", "*.JPEG", "*.WEBP", "*.BMP"]
    return sum(len(list((BASE_DIR / "imagenes").rglob(ext))) for ext in exts)


def contar_raw():
    exts = ["*.fit", "*.FIT", "*.csv", "*.CSV", "*.xlsx", "*.xls", "*.txt"]
    return sum(len(list((BASE_DIR / "raw").rglob(ext))) for ext in exts)


def contar_excels_resultados():
    return len(list((BASE_DIR / "resultados").rglob("*.xlsx")))


def estado_proyecto():
    fotos = contar_imagenes()
    raw = contar_raw()
    excels = contar_excels_resultados()

    print("\n===========================================")
    print(" ESTADO DEL PROYECTO")
    print("===========================================")
    print(f"Carpeta proyecto: {BASE_DIR}")
    print(f"Versión: {VERSION}")
    print("")
    print(f"Fotos detectadas:        {fotos}")
    print(f"RAW detectados:          {raw}")
    print(f"Excels generados:        {excels}")
    print("")
    print(f"OCR:                     {'OK' if fotos > 0 and excels > 0 else 'Pendiente'}")
    print(f"RAW:                     {'OK' if raw > 0 else 'Pendiente'}")
    print(f"Comparación EDGE-CLOUD:  {'Pendiente' if raw == 0 else 'Preparada'}")
    print("===========================================\n")


def menu():
    asegurar_estructura()

    while True:
        print("\n===========================================")
        print(f" SPORTSLIFE7 QC - EDGE vs CLOUD v{VERSION}")
        print("===========================================")
        print(f"Carpeta proyecto: {BASE_DIR}")
        print(f"Fotos detectadas: {contar_imagenes()}")
        print(f"RAW detectados:   {contar_raw()}")
        print("")
        print("1. Analizar proyecto completo")
        print("2. Procesar imágenes EDGE")
        print("3. Procesar archivos RAW")
        print("4. Comparar EDGE vs CLOUD")
        print("5. Abrir carpeta Resultados")
        print("6. Abrir carpeta Imágenes")
        print("7. Abrir carpeta RAW")
        print("8. Estado del proyecto")
        print("0. Salir")

        op = input("\nSelecciona opción: ").strip()

        try:
            if op == "1":
                ejecutar_ocr()
                procesar_raw(BASE_DIR)
                comparar_edge_cloud(BASE_DIR)
                pausa()
            elif op == "2":
                ejecutar_ocr()
                pausa()
            elif op == "3":
                procesar_raw(BASE_DIR)
                pausa()
            elif op == "4":
                comparar_edge_cloud(BASE_DIR)
                pausa()
            elif op == "5":
                abrir_carpeta(BASE_DIR / "resultados")
            elif op == "6":
                abrir_carpeta(BASE_DIR / "imagenes")
            elif op == "7":
                abrir_carpeta(BASE_DIR / "raw")
            elif op == "8":
                estado_proyecto()
                pausa()
            elif op == "0":
                break
            else:
                print("Opción no válida.")
        except Exception:
            print("ERROR DURANTE LA EJECUCIÓN")
            print(traceback.format_exc())
            pausa()


if __name__ == "__main__":
    menu()