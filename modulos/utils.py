# -*- coding: utf-8 -*-
from pathlib import Path
import os
import subprocess
import sys


def abrir_carpeta(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        os.startfile(str(path))
    elif sys.platform == 'darwin':
        subprocess.run(['open', str(path)], check=False)
    else:
        subprocess.run(['xdg-open', str(path)], check=False)


def pausa():
    input('\nPulsa Enter para continuar...')
