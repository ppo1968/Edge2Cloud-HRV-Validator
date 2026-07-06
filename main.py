# -*- coding: utf-8 -*-
from pathlib import Path
import traceback

from modulos.modulo_ocr import ejecutar_ocr
from modulos.modulo_raw import procesar_raw
from modulos.modulo_comparacion import comparar_edge_cloud
from modulos.utils import abrir_carpeta, pausa

BASE_DIR = Path(__file__).resolve().parent


def asegurar_estructura():
    for carpeta in ['imagenes', 'raw', 'resultados', 'modulos']:
        (BASE_DIR / carpeta).mkdir(parents=True, exist_ok=True)


def contar_imagenes():
    exts = ['*.png','*.jpg','*.jpeg','*.webp','*.bmp','*.PNG','*.JPG','*.JPEG','*.WEBP','*.BMP']
    total = 0
    for ext in exts:
        total += len(list((BASE_DIR / 'imagenes').rglob(ext)))
    return total


def contar_raw():
    total = 0
    for ext in ['*.xlsx','*.xls','*.csv','*.txt']:
        total += len(list((BASE_DIR / 'raw').glob(ext)))
    return total


def menu():
    asegurar_estructura()
    while True:
        print('\n===========================================')
        print(' SPORTSLIFE7 QC - EDGE vs CLOUD')
        print('===========================================')
        print(f'Carpeta proyecto: {BASE_DIR}')
        print(f'Fotos detectadas: {contar_imagenes()}')
        print(f'RAW detectados:   {contar_raw()}')
        print('')
        print('1. Extraer datos EDGE desde fotos')
        print('2. Calcular CLOUD desde RAW')
        print('3. Comparar EDGE vs CLOUD')
        print('4. Ejecutar todo')
        print('5. Abrir carpeta Resultados')
        print('6. Abrir carpeta Imágenes')
        print('7. Abrir carpeta RAW')
        print('0. Salir')
        op = input('\nSelecciona opción: ').strip()

        try:
            if op == '1':
                ejecutar_ocr()
                pausa()
            elif op == '2':
                procesar_raw(BASE_DIR)
                pausa()
            elif op == '3':
                comparar_edge_cloud(BASE_DIR)
                pausa()
            elif op == '4':
                ejecutar_ocr()
                procesar_raw(BASE_DIR)
                comparar_edge_cloud(BASE_DIR)
                pausa()
            elif op == '5':
                abrir_carpeta(BASE_DIR / 'resultados')
            elif op == '6':
                abrir_carpeta(BASE_DIR / 'imagenes')
            elif op == '7':
                abrir_carpeta(BASE_DIR / 'raw')
            elif op == '0':
                break
            else:
                print('Opción no válida.')
        except Exception:
            print('ERROR DURANTE LA EJECUCIÓN')
            print(traceback.format_exc())
            pausa()


if __name__ == '__main__':
    menu()
