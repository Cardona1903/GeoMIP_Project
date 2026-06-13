"""
Interfaz gráfica para KQNodes / KGeoMIP
Análisis de k-Particiones Óptimas — ADA 2026-1
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import csv
import sys
import queue
import concurrent.futures
from math import comb, factorial
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.models.system import System
    from src.controllers.strategies.geometric import KGeoMIP, KGeoMIPKPartition
    from src.controllers.strategies.qnodes import KQNodes
    MODULES_OK = True
    MODULES_ERROR = None
except Exception as exc:
    MODULES_OK = False
    MODULES_ERROR = str(exc)

# ── Paleta de colores científica (estilo dark scientific) ─────────────────────
COLORS = {
    'bg_main':       '#0d1117',
    'bg_panel':      '#161b22',
    'bg_input':      '#21262d',
    'bg_hover':      '#30363d',
    'accent':        '#238636',
    'accent_light':  '#2ea043',
    'danger':        '#da3633',
    'warning':       '#d29922',
    'info':          '#388bfd',
    'text_primary':  '#c9d1d9',
    'text_secondary':'#8b949e',
    'text_accent':   '#58a6ff',
    'border':        '#30363d',
    'success':       '#3fb950',
    'log_cmd':       '#58a6ff',
    'log_result':    '#3fb950',
    'log_warning':   '#d29922',
    'log_error':     '#f85149',
    'phi_zero':      '#3fb950',
    'phi_nonzero':   '#d29922',
}

# ── Configuraciones predefinidas del Excel ──────────────────────────────────
PREDEFINIDOS = {
    "N=10": {
        "sistema": "ABCDEFGHIJ",
        "estado":  "1000000000",
        "csv":     "data/N10C.csv",
    },
    "N=15": {
        "sistema": "ABCDEFGHIJKLMNO",
        "estado":  "100000000000000",
        "csv":     "data/N15C.csv",
    },
    "N=20": {
        "sistema": "ABCDEFGHIJKLMNOPQRST",
        "estado":  "10000000000000000000",
        "csv":     "data/N20C.csv",
    },
    "N=22": {
        "sistema": "ABCDEFGHIJKLMNOPQRSTUV",
        "estado":  "1000000000000000000000",
        "csv":     "data/N22C.csv",
    },
    "N=25": {
        "sistema": "ABCDEFGHIJKLMNOPQRSTUVWXY",
        "estado":  "1000000000000000000000000",
        "csv":     "data/N25C.csv",
    },
}

# ── Hojas Excel por N ──────────────────────────────────────────────────────
HOJAS_EXCEL = {
    10: '10A-Elementos',
    15: '15B-Elementos',
    20: '20A-Elementos',
    22: '22A-Elementos',
    25: '25A-Elementos ',
}

# ── Suites de pruebas predefinidas ────────────────────────────────────────
SUITES = {
    'N=10': {
        'sistema': 'ABCDEFGHIJ',
        'estado':  '1000000000',
        'csv':     'data/N10C.csv',
        'pruebas': [
            ('ABCDEFGHIJ', 'ABCDEFGHIJ'), ('ABCDEFGHIJ', 'ABCDEFGHI'),
            ('ABCDEFGHIJ', 'BCDEFGHIJ'),  ('ABCDEFGHIJ', 'BCDEFGHI'),
            ('ABCDEFGHIJ', 'ABDEGHJ'),    ('ABCDEFGHIJ', 'ACEGI'),
            ('ABCDEFGHIJ', 'BDFHJ'),      ('ABCDEFGHI',  'ABCDEFGHIJ'),
            ('ABCDEFGHI',  'ABCDEFGHI'),  ('ABCDEFGHI',  'BCDEFGHIJ'),
            ('ABCDEFGHI',  'BCDEFGHI'),   ('ABCDEFGHI',  'ABDEGHJ'),
            ('ABCDEFGHI',  'ACEGI'),      ('ABCDEFGHI',  'BDFHJ'),
            ('BCDEFGHIJ',  'ABCDEFGHIJ'), ('BCDEFGHIJ',  'ABCDEFGHI'),
            ('BCDEFGHIJ',  'BCDEFGHIJ'),  ('BCDEFGHIJ',  'BCDEFGHI'),
            ('BCDEFGHIJ',  'ABDEGHJ'),    ('BCDEFGHIJ',  'ACEGI'),
            ('BCDEFGHIJ',  'BDFHJ'),      ('BCDEFGHI',   'ABCDEFGHIJ'),
            ('BCDEFGHI',   'ABCDEFGHI'),  ('BCDEFGHI',   'BCDEFGHIJ'),
            ('BCDEFGHI',   'BCDEFGHI'),   ('BCDEFGHI',   'ABDEGHJ'),
            ('BCDEFGHI',   'ACEGI'),      ('BCDEFGHI',   'BDFHJ'),
            ('ABDEGHJ',    'ABCDEFGHIJ'), ('ABDEGHJ',    'ABCDEFGHI'),
            ('ABDEGHJ',    'BCDEFGHIJ'),  ('ABDEGHJ',    'BCDEFGHI'),
            ('ABDEGHJ',    'ABDEGHJ'),    ('ABDEGHJ',    'ACEGI'),
            ('ABDEGHJ',    'BDFHJ'),      ('ACEGI',      'ABCDEFGHIJ'),
            ('ACEGI',      'ABCDEFGHI'),  ('ACEGI',      'BCDEFGHIJ'),
            ('ACEGI',      'BCDEFGHI'),   ('ACEGI',      'ABDEGHJ'),
            ('ACEGI',      'ACEGI'),      ('ACEGI',      'BDFHJ'),
            ('BDFHJ',      'ABCDEFGHIJ'), ('BDFHJ',      'ABCDEFGHI'),
            ('BDFHJ',      'BCDEFGHIJ'),  ('BDFHJ',      'BCDEFGHI'),
            ('BDFHJ',      'ABDEGHJ'),    ('BDFHJ',      'ACEGI'),
            ('BDFHJ',      'BDFHJ'),
        ],
    },
    'N=15': {
        'sistema': 'ABCDEFGHIJKLMNO',
        'estado':  '100000000000000',
        'csv':     'data/N15C.csv',
        'pruebas': [
            ('ABCDEFGHIJKLMNO', 'ABCDEFGHIJKLMNO'), ('ABCDEFGHIJKLMNO', 'ABCDEFGHIJKLMN'),
            ('ABCDEFGHIJKLMNO', 'BCDEFGHIJKLMNO'),  ('ABCDEFGHIJKLMNO', 'BCDEFGHIJKLMN'),
            ('ABCDEFGHIJKLMNO', 'ABDEGHJKMN'),       ('ABCDEFGHIJKLMNO', 'ACEGIKMO'),
            ('ABCDEFGHIJKLMNO', 'BDFHJLN'),          ('ABCDEFGHIJKLMN',  'ABCDEFGHIJKLMNO'),
            ('ABCDEFGHIJKLMN',  'ABCDEFGHIJKLMN'),  ('ABCDEFGHIJKLMN',  'BCDEFGHIJKLMNO'),
            ('ABCDEFGHIJKLMN',  'BCDEFGHIJKLMN'),   ('ABCDEFGHIJKLMN',  'ABDEGHJKMN'),
            ('ABCDEFGHIJKLMN',  'ACEGIKMO'),         ('ABCDEFGHIJKLMN',  'BDFHJLN'),
            ('BCDEFGHIJKLMNO',  'ABCDEFGHIJKLMNO'), ('BCDEFGHIJKLMNO',  'ABCDEFGHIJKLMN'),
            ('BCDEFGHIJKLMNO',  'BCDEFGHIJKLMNO'),  ('BCDEFGHIJKLMNO',  'BCDEFGHIJKLMN'),
            ('BCDEFGHIJKLMNO',  'ABDEGHJKMN'),       ('BCDEFGHIJKLMNO',  'ACEGIKMO'),
            ('BCDEFGHIJKLMNO',  'BDFHJLN'),          ('BCDEFGHIJKLMN',   'ABCDEFGHIJKLMNO'),
            ('BCDEFGHIJKLMN',   'ABCDEFGHIJKLMN'),  ('BCDEFGHIJKLMN',   'BCDEFGHIJKLMNO'),
            ('BCDEFGHIJKLMN',   'BCDEFGHIJKLMN'),   ('BCDEFGHIJKLMN',   'ABDEGHJKMN'),
            ('BCDEFGHIJKLMN',   'ACEGIKMO'),         ('BCDEFGHIJKLMN',   'BDFHJLN'),
            ('ABDEGHJKMN',      'ABCDEFGHIJKLMNO'), ('ABDEGHJKMN',      'ABCDEFGHIJKLMN'),
            ('ABDEGHJKMN',      'BCDEFGHIJKLMNO'),  ('ABDEGHJKMN',      'BCDEFGHIJKLMN'),
            ('ABDEGHJKMN',      'ABDEGHJKMN'),       ('ABDEGHJKMN',      'ACEGIKMO'),
            ('ABDEGHJKMN',      'BDFHJLN'),          ('ACEGIKMO',        'ABCDEFGHIJKLMNO'),
            ('ACEGIKMO',        'ABCDEFGHIJKLMN'),  ('ACEGIKMO',        'BCDEFGHIJKLMNO'),
            ('ACEGIKMO',        'BCDEFGHIJKLMN'),   ('ACEGIKMO',        'ABDEGHJKMN'),
            ('ACEGIKMO',        'ACEGIKMO'),         ('ACEGIKMO',        'BDFHJLN'),
            ('BDFHJLN',         'ABCDEFGHIJKLMNO'), ('BDFHJLN',         'ABCDEFGHIJKLMN'),
            ('BDFHJLN',         'BCDEFGHIJKLMNO'),  ('BDFHJLN',         'BCDEFGHIJKLMN'),
            ('BDFHJLN',         'ABDEGHJKMN'),       ('BDFHJLN',         'ACEGIKMO'),
            ('BDFHJLN',         'BDFHJLN'),          ('BCDEFGJKLMNO',    'BCDEFGHIJKLMNO'),
        ],
    },
    'N=20': {
        'sistema': 'ABCDEFGHIJKLMNOPQRST',
        'estado':  '10000000000000000000',
        'csv':     'data/N20C.csv',
        'pruebas': [
            ('ABCDEFGHIJKLMNOPQRST', 'ABCDEFGHIJKLMNOPQRST'),
            ('ABCDEFGHIJKLMNOPQRST', 'ABCDEFGHIJKLMNOPQRS'),
            ('ABCDEFGHIJKLMNOPQRST', 'BCDEFGHIJKLMNOPQRST'),
            ('ABCDEFGHIJKLMNOPQRST', 'BCDEFGHIJKLMNOPQRS'),
            ('ABCDEFGHIJKLMNOPQRST', 'ABDEGHJKMNPQST'),
            ('ABCDEFGHIJKLMNOPQRST', 'ACEGIKMOQS'),
            ('ABCDEFGHIJKLMNOPQRST', 'BDFHJLNPRT'),
            ('ABCDEFGHIJKLMNOPQRS',  'ABCDEFGHIJKLMNOPQRST'),
            ('ABCDEFGHIJKLMNOPQRS',  'ABCDEFGHIJKLMNOPQRS'),
            ('ABCDEFGHIJKLMNOPQRS',  'BCDEFGHIJKLMNOPQRST'),
            ('ABCDEFGHIJKLMNOPQRS',  'BCDEFGHIJKLMNOPQRS'),
            ('ABCDEFGHIJKLMNOPQRS',  'ABDEGHJKMNPQST'),
            ('ABCDEFGHIJKLMNOPQRS',  'ACEGIKMOQS'),
            ('ABCDEFGHIJKLMNOPQRS',  'BDFHJLNPRT'),
            ('BCDEFGHIJKLMNOPQRST',  'ABCDEFGHIJKLMNOPQRST'),
            ('BCDEFGHIJKLMNOPQRST',  'ABCDEFGHIJKLMNOPQRS'),
            ('BCDEFGHIJKLMNOPQRST',  'BCDEFGHIJKLMNOPQRST'),
            ('BCDEFGHIJKLMNOPQRST',  'BCDEFGHIJKLMNOPQRS'),
            ('BCDEFGHIJKLMNOPQRST',  'ABDEGHJKMNPQST'),
            ('BCDEFGHIJKLMNOPQRST',  'ACEGIKMOQS'),
            ('BCDEFGHIJKLMNOPQRST',  'BDFHJLNPRT'),
            ('BCDEFGHIJKLMNOPQRS',   'ABCDEFGHIJKLMNOPQRST'),
            ('BCDEFGHIJKLMNOPQRS',   'ABCDEFGHIJKLMNOPQRS'),
            ('BCDEFGHIJKLMNOPQRS',   'BCDEFGHIJKLMNOPQRST'),
            ('BCDEFGHIJKLMNOPQRS',   'BCDEFGHIJKLMNOPQRS'),
            ('BCDEFGHIJKLMNOPQRS',   'ABDEGHJKMNPQST'),
            ('BCDEFGHIJKLMNOPQRS',   'ACEGIKMOQS'),
            ('BCDEFGHIJKLMNOPQRS',   'BDFHJLNPRT'),
            ('ABDEGHJKMNPQST',       'ABCDEFGHIJKLMNOPQRST'),
            ('ABDEGHJKMNPQST',       'ABCDEFGHIJKLMNOPQRS'),
            ('ABDEGHJKMNPQST',       'BCDEFGHIJKLMNOPQRST'),
            ('ABDEGHJKMNPQST',       'BCDEFGHIJKLMNOPQRS'),
            ('ABDEGHJKMNPQST',       'ABDEGHJKMNPQST'),
            ('ABDEGHJKMNPQST',       'ACEGIKMOQS'),
            ('ABDEGHJKMNPQST',       'BDFHJLNPRT'),
            ('ACEGIKMOQS',           'ABCDEFGHIJKLMNOPQRST'),
            ('ACEGIKMOQS',           'ABCDEFGHIJKLMNOPQRS'),
            ('ACEGIKMOQS',           'BCDEFGHIJKLMNOPQRST'),
            ('ACEGIKMOQS',           'BCDEFGHIJKLMNOPQRS'),
            ('ACEGIKMOQS',           'ABDEGHJKMNPQST'),
            ('ACEGIKMOQS',           'ACEGIKMOQS'),
            ('ACEGIKMOQS',           'BDFHJLNPRT'),
            ('BDFHJLNPRT',           'ABCDEFGHIJKLMNOPQRST'),
            ('BDFHJLNPRT',           'ABCDEFGHIJKLMNOPQRS'),
            ('BDFHJLNPRT',           'BCDEFGHIJKLMNOPQRST'),
            ('BDFHJLNPRT',           'BCDEFGHIJKLMNOPQRS'),
            ('BDFHJLNPRT',           'ABDEGHJKMNPQST'),
            ('BDFHJLNPRT',           'ACEGIKMOQS'),
            ('BDFHJLNPRT',           'BDFHJLNPRT'),
            ('BCDEFGJKLMNO',         'BCDEFGHIJKLMNO'),
        ],
    },
    'N=22': {
        'sistema': 'ABCDEFGHIJKLMNOPQRSTUV',
        'estado':  '1000000000000000000000',
        'csv':     'data/N22C.csv',
        'pruebas': [
            ('ABCDEFGHIJKLMNOPQRSTUV', 'ABCDEFGHIJKLMNOPQRSTUV'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'ABCDEFGHIJKLMNOPQRSTU'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'BCDEFGHIJKLMNOPQRSTUV'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'BCDEFGHIJKLMNOPQRSTU'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'ABDEGHJKMNPQSTV'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'ACEGIKMOQSU'),
            ('ABCDEFGHIJKLMNOPQRSTUV', 'BDFHJLNPRTV'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'ABCDEFGHIJKLMNOPQRSTUV'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'ABCDEFGHIJKLMNOPQRSTU'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'BCDEFGHIJKLMNOPQRSTUV'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'BCDEFGHIJKLMNOPQRSTU'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'ABDEGHJKMNPQSTV'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'ACEGIKMOQSU'),
            ('ABCDEFGHIJKLMNOPQRSTU',  'BDFHJLNPRTV'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'ABCDEFGHIJKLMNOPQRSTUV'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'ABCDEFGHIJKLMNOPQRSTU'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'BCDEFGHIJKLMNOPQRSTUV'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'BCDEFGHIJKLMNOPQRSTU'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'ABDEGHJKMNPQSTV'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'ACEGIKMOQSU'),
            ('BCDEFGHIJKLMNOPQRSTUV',  'BDFHJLNPRTV'),
            ('BCDEFGHIJKLMNOPQRSTU',   'ABCDEFGHIJKLMNOPQRSTUV'),
            ('BCDEFGHIJKLMNOPQRSTU',   'ABCDEFGHIJKLMNOPQRSTU'),
            ('BCDEFGHIJKLMNOPQRSTU',   'BCDEFGHIJKLMNOPQRSTUV'),
            ('BCDEFGHIJKLMNOPQRSTU',   'BCDEFGHIJKLMNOPQRSTU'),
            ('BCDEFGHIJKLMNOPQRSTU',   'ABDEGHJKMNPQSTV'),
            ('BCDEFGHIJKLMNOPQRSTU',   'ACEGIKMOQSU'),
            ('BCDEFGHIJKLMNOPQRSTU',   'BDFHJLNPRTV'),
            ('ABDEGHJKMNPQSTV',        'ABCDEFGHIJKLMNOPQRSTUV'),
            ('ABDEGHJKMNPQSTV',        'ABCDEFGHIJKLMNOPQRSTU'),
            ('ABDEGHJKMNPQSTV',        'BCDEFGHIJKLMNOPQRSTUV'),
            ('ABDEGHJKMNPQSTV',        'BCDEFGHIJKLMNOPQRSTU'),
            ('ABDEGHJKMNPQSTV',        'ABDEGHJKMNPQSTV'),
            ('ABDEGHJKMNPQSTV',        'ACEGIKMOQSU'),
            ('ABDEGHJKMNPQSTV',        'BDFHJLNPRTV'),
            ('ACEGIKMOQSU',            'ABCDEFGHIJKLMNOPQRSTUV'),
            ('ACEGIKMOQSU',            'ABCDEFGHIJKLMNOPQRSTU'),
            ('ACEGIKMOQSU',            'BCDEFGHIJKLMNOPQRSTUV'),
            ('ACEGIKMOQSU',            'BCDEFGHIJKLMNOPQRSTU'),
            ('ACEGIKMOQSU',            'ABDEGHJKMNPQSTV'),
            ('ACEGIKMOQSU',            'ACEGIKMOQSU'),
            ('ACEGIKMOQSU',            'BDFHJLNPRTV'),
            ('BDFHJLNPRTV',            'ABCDEFGHIJKLMNOPQRSTUV'),
            ('BDFHJLNPRTV',            'ABCDEFGHIJKLMNOPQRSTU'),
            ('BDFHJLNPRTV',            'BCDEFGHIJKLMNOPQRSTUV'),
            ('BDFHJLNPRTV',            'BCDEFGHIJKLMNOPQRSTU'),
            ('BDFHJLNPRTV',            'ABDEGHJKMNPQSTV'),
            ('BDFHJLNPRTV',            'ACEGIKMOQSU'),
            ('BDFHJLNPRTV',            'BDFHJLNPRTV'),
            ('ACDEFGHIJKLMNOPQRST',    'ACDEFGHIJKLMNOPQRST'),
        ],
    },
    'N=25': {
        'sistema':   'ABCDEFGHIJKLMNOPQRSTUVWXY',
        'estado':    '1000000000000000000000000',
        'csv':       'data/N25C.csv',
        'n_sistema': 25,
        'pruebas': [
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'ABDEGHJKMNPQSTVWY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'ACEGIKMOQSUWY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXY', 'BDFHJLNPRTVX'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'ABDEGHJKMNPQSTVWY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'ACEGIKMOQSUWY'),
            ('ABCDEFGHIJKLMNOPQRSTUVWX',  'BDFHJLNPRTVX'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'ABDEGHJKMNPQSTVWY'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'ACEGIKMOQSUWY'),
            ('BCDEFGHIJKLMNOPQRSTUVWXY',  'BDFHJLNPRTVX'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'ABDEGHJKMNPQSTVWY'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'ACEGIKMOQSUWY'),
            ('BCDEFGHIJKLMNOPQRSTUVWX',   'BDFHJLNPRTVX'),
            ('ABDEGHJKMNPQSTVWY',         'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABDEGHJKMNPQSTVWY',         'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABDEGHJKMNPQSTVWY',         'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ABDEGHJKMNPQSTVWY',         'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('ABDEGHJKMNPQSTVWY',         'ABDEGHJKMNPQSTVWY'),
            ('ABDEGHJKMNPQSTVWY',         'ACEGIKMOQSUWY'),
            ('ABDEGHJKMNPQSTVWY',         'BDFHJLNPRTVX'),
            ('ACEGIKMOQSUWY',             'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ACEGIKMOQSUWY',             'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('ACEGIKMOQSUWY',             'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('ACEGIKMOQSUWY',             'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('ACEGIKMOQSUWY',             'ABDEGHJKMNPQSTVWY'),
            ('ACEGIKMOQSUWY',             'ACEGIKMOQSUWY'),
            ('ACEGIKMOQSUWY',             'BDFHJLNPRTVX'),
            ('BDFHJLNPRTVX',             'ABCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BDFHJLNPRTVX',             'ABCDEFGHIJKLMNOPQRSTUVWX'),
            ('BDFHJLNPRTVX',             'BCDEFGHIJKLMNOPQRSTUVWXY'),
            ('BDFHJLNPRTVX',             'BCDEFGHIJKLMNOPQRSTUVWX'),
            ('BDFHJLNPRTVX',             'ABDEGHJKMNPQSTVWY'),
            ('BDFHJLNPRTVX',             'ACEGIKMOQSUWY'),
            ('BDFHJLNPRTVX',             'BDFHJLNPRTVX'),
            ('ACDEFGHIJKLMNOPQRSTVX',    'ACDEFGHIJKLMNOPQRSTVX'),
        ],
    },
}

# ── Stirling de segunda especie S(n,k) ─────────────────────────────────────
def stirling2(n: int, k: int) -> int:
    if k == 0:
        return 1 if n == 0 else 0
    if k > n:
        return 0
    return sum((-1) ** (k - j) * comb(k, j) * (j ** n)
               for j in range(k + 1)) // factorial(k)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KQNodes / KGeoMIP — Análisis de k-Particiones Óptimas")
        self.minsize(1100, 720)
        self.geometry("1280x800")
        self.resizable(True, True)
        self.configure(bg=COLORS['bg_main'])

        self._q: queue.Queue = queue.Queue()
        self._results: list  = []
        self._updating_predefined = False
        self._excel_rows: list = []
        self._prueba_counter: int = 0
        # Referencias a los últimos resultados (usadas por exportar_a_excel)
        self._ultimo_res_geo      = None
        self._ultimo_res_geo_full = None
        self._ultimo_res_qn       = None
        self._ultimo_sub       = None
        self._ultimo_t_geo     = 0.0
        self._ultimo_t_qn      = 0.0
        self._ultimo_n_sistema = 0
        self._ultimo_sistema   = ''
        # Historial de todos los análisis ejecutados
        self._historial_analisis: list = []

        self._build_ui()

        if not MODULES_OK:
            messagebox.showwarning(
                "Módulos no disponibles",
                f"No se pudieron cargar los módulos del proyecto:\n{MODULES_ERROR}\n\n"
                "Asegúrate de ejecutar desde el directorio raíz del proyecto."
            )

        self._poll()

    # ── Construcción de UI ─────────────────────────────────────────────────

    def _build_ui(self):
        C = COLORS
        root = tk.Frame(self, bg=C['bg_main'])
        root.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        left = tk.LabelFrame(
            root,
            text="Configuración del Sistema",
            font=('Segoe UI', 10, 'bold'),
            bg=C['bg_panel'], fg=C['text_primary'],
            bd=1, padx=12, pady=8,
        )
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        left.configure(width=400)

        right = tk.LabelFrame(
            root,
            text="Resultados",
            font=('Segoe UI', 10, 'bold'),
            bg=C['bg_panel'], fg=C['text_primary'],
            bd=1, padx=10, pady=8,
        )
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left(left)
        self._build_right(right)
        self._build_bottom()

    def _build_left(self, p):
        C = COLORS
        row = 0

        tk.Label(
            p,
            text="KQNodes / KGeoMIP  v1.0\n"
                 "Análisis de k-Particiones Óptimas\n"
                 "Análisis y Diseño de Algoritmos 2026-1",
            font=('Segoe UI', 9),
            fg=C['text_secondary'], bg=C['bg_panel'],
            justify=tk.CENTER,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1

        tk.Frame(p, height=1, bg=C['border']).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1

        tk.Label(
            p, text="Sistema predefinido:", anchor="w",
            font=('Segoe UI', 9, 'bold'),
            fg=C['text_primary'], bg=C['bg_panel'],
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 2))
        row += 1

        self._n_var = tk.StringVar(value="— seleccionar —")
        opts = ["— seleccionar —"] + list(PREDEFINIDOS) + ["Personalizado"]
        om = tk.OptionMenu(p, self._n_var, *opts, command=self._on_n)
        om.config(
            width=26,
            bg=C['bg_input'], fg=C['text_primary'],
            activebackground=C['bg_hover'], activeforeground=C['text_primary'],
            font=('Segoe UI', 9),
            relief=tk.FLAT, bd=1,
            highlightbackground=C['border'], highlightthickness=1,
        )
        om['menu'].config(
            bg=C['bg_input'], fg=C['text_primary'],
            activebackground=C['bg_hover'], activeforeground=C['text_primary'],
            font=('Segoe UI', 9),
        )
        om.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1

        def field(label_text, attr, row_):
            tk.Label(
                p, text=label_text, anchor="w",
                font=('Segoe UI', 9),
                fg=C['text_secondary'], bg=C['bg_panel'],
            ).grid(row=row_, column=0, columnspan=2, sticky="w", pady=(4, 1))
            row_ += 1
            var = tk.StringVar()
            tk.Entry(
                p, textvariable=var, width=34,
                bg=C['bg_input'], fg=C['text_primary'],
                insertbackground=C['text_primary'],
                relief=tk.FLAT, font=('Segoe UI', 9),
                highlightbackground=C['border'], highlightthickness=1,
            ).grid(row=row_, column=0, columnspan=2, sticky="ew")
            setattr(self, attr, var)
            return row_ + 1

        row = field("Sistema completo (variables):", "_sys_var", row)
        row = field("Estado inicial (binario):",     "_est_var", row)

        tk.Label(
            p, text="Ruta CSV:", anchor="w",
            font=('Segoe UI', 9),
            fg=C['text_secondary'], bg=C['bg_panel'],
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 1))
        row += 1

        self._csv_var = tk.StringVar()
        cf = tk.Frame(p, bg=C['bg_panel'])
        cf.grid(row=row, column=0, columnspan=2, sticky="ew")
        tk.Entry(
            cf, textvariable=self._csv_var, width=24,
            bg=C['bg_input'], fg=C['text_primary'],
            insertbackground=C['text_primary'],
            relief=tk.FLAT, font=('Segoe UI', 9),
            highlightbackground=C['border'], highlightthickness=1,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(
            cf, text="Buscar…", command=self._browse,
            bg=C['bg_hover'], fg=C['text_primary'],
            activebackground=C['border'], activeforeground=C['text_primary'],
            relief=tk.FLAT, font=('Segoe UI', 8), padx=6, pady=3,
        ).pack(side=tk.RIGHT, padx=(4, 0))
        row += 1

        self._csv_status_lbl = tk.Label(
            p, text="", anchor="w",
            font=('Segoe UI', 8),
            fg=C['text_secondary'], bg=C['bg_panel'],
        )
        self._csv_status_lbl.grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(1, 4))
        row += 1

        row = field("Alcance (t+1):",  "_alc_var", row)
        row = field("Mecanismo (t):",  "_mec_var", row)

        tk.Frame(p, height=1, bg=C['border']).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        tk.Label(
            p, text="Estrategias:", anchor="w",
            font=('Segoe UI', 9, 'bold'),
            fg=C['text_primary'], bg=C['bg_panel'],
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        self._use_geo  = tk.BooleanVar(value=True)
        self._use_qnod = tk.BooleanVar(value=True)

        for text, var in [
            ("KGeoMIP (k=2)    — bipartición óptima",   self._use_geo),
            ("KQNodes (k=3,4,5) — k-partición óptima",  self._use_qnod),
        ]:
            tk.Checkbutton(
                p, text=text, variable=var,
                bg=C['bg_panel'], fg=C['text_primary'],
                selectcolor=C['bg_input'],
                activebackground=C['bg_panel'], activeforeground=C['text_primary'],
                font=('Segoe UI', 9),
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
            row += 1

        tk.Label(p, text="", bg=C['bg_panel']).grid(row=row)
        row += 1

        self._btn_run = tk.Button(
            p, text="▶  Ejecutar análisis",
            font=('Segoe UI', 11, 'bold'),
            bg=C['accent'], fg="white",
            activebackground=C['accent_light'], activeforeground="white",
            relief=tk.FLAT, command=self._run,
            padx=8, pady=9, cursor="hand2",
        )
        self._btn_run.grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        row += 1

        self._btn_suite = tk.Button(
            p, text="⚡ Ejecutar suite",
            font=('Segoe UI', 10, 'bold'),
            bg='#1f6feb', fg="white",
            activebackground='#388bfd', activeforeground="white",
            relief=tk.FLAT, command=self._ejecutar_suite,
            padx=8, pady=7, cursor="hand2",
        )
        self._btn_suite.grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        row += 1

        tk.Button(
            p, text="Limpiar todo", command=self._clear,
            bg=C['bg_hover'], fg=C['text_secondary'],
            activebackground=C['border'], activeforeground=C['text_primary'],
            relief=tk.FLAT, font=('Segoe UI', 9),
            padx=8, pady=5,
        ).grid(row=row, column=0, columnspan=2, sticky="ew")

        p.columnconfigure(0, weight=1)

        # ── Trazas ────────────────────────────────────────────────────────
        def _on_campo_modificado(*args):
            if self._updating_predefined:
                return
            actual_sis = self._sys_var.get()
            actual_est = self._est_var.get()
            actual_alc = self._alc_var.get()
            actual_mec = self._mec_var.get()
            for nombre, vals in PREDEFINIDOS.items():
                pred_alc = vals.get('alcance', vals['sistema'])
                pred_mec = vals.get('mecanismo', vals['sistema'])
                if (actual_sis == vals['sistema'] and
                        actual_est == vals['estado']  and
                        actual_alc == pred_alc        and
                        actual_mec == pred_mec):
                    if self._n_var.get() != nombre:
                        self._n_var.set(nombre)
                    return
            self._n_var.set('Personalizado')

        for var in [self._sys_var, self._est_var,
                    self._alc_var, self._mec_var]:
            var.trace_add('write', _on_campo_modificado)

        self._csv_var.trace_add(
            'write', lambda *a: self._actualizar_csv_status())

    def _build_right(self, p):
        C = COLORS

        # ── Estilos ttk ───────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Dark.Treeview",
                        background=C['bg_input'],
                        foreground=C['text_primary'],
                        fieldbackground=C['bg_input'],
                        rowheight=22,
                        font=('Consolas', 9))
        style.configure("Dark.Treeview.Heading",
                        background=C['bg_hover'],
                        foreground=C['text_accent'],
                        font=('Segoe UI', 9, 'bold'),
                        relief='flat')
        style.map("Dark.Treeview",
                  background=[('selected', C['bg_hover'])],
                  foreground=[('selected', C['text_primary'])])
        style.configure("TProgressbar",
                        background=C['accent'],
                        troughcolor=C['bg_input'],
                        bordercolor=C['border'],
                        lightcolor=C['accent'],
                        darkcolor=C['accent'])
        style.configure("Dark.TNotebook",
                        background=C['bg_panel'],
                        tabmargins=[2, 4, 2, 0])
        style.configure("Dark.TNotebook.Tab",
                        background=C['bg_input'],
                        foreground=C['text_secondary'],
                        padding=[10, 4],
                        font=('Segoe UI', 9, 'bold'))
        style.map("Dark.TNotebook.Tab",
                  background=[('selected', C['bg_hover']),
                               ('active',   C['bg_hover'])],
                  foreground=[('selected', C['text_accent']),
                               ('active',   C['text_primary'])])

        # ── Log ───────────────────────────────────────────────────────────
        log_frm = tk.LabelFrame(
            p, text="Progreso en tiempo real",
            font=('Segoe UI', 10, 'bold'),
            bg=C['bg_panel'], fg=C['text_primary'],
            bd=1, padx=6, pady=6,
        )
        log_frm.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self._log = tk.Text(
            log_frm, height=9, wrap=tk.WORD,
            state=tk.DISABLED,
            bg=C['bg_main'], fg=C['text_primary'],
            font=('Consolas', 10), relief=tk.FLAT,
            insertbackground=C['text_primary'],
            selectbackground=C['bg_hover'],
        )
        log_sb = tk.Scrollbar(log_frm, command=self._log.yview,
                              bg=C['bg_panel'])
        self._log.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log.pack(fill=tk.BOTH, expand=True)

        self._log.tag_config("ok",   foreground=C['log_result'])
        self._log.tag_config("warn", foreground=C['log_warning'])
        self._log.tag_config("err",  foreground=C['log_error'])
        self._log.tag_config("info", foreground=C['log_cmd'])

        # ── Tabla de resultados ────────────────────────────────────────────
        tbl_frm = tk.LabelFrame(
            p, text="Tabla de resultados",
            font=('Segoe UI', 10, 'bold'),
            bg=C['bg_panel'], fg=C['text_primary'],
            bd=1, padx=6, pady=6,
        )
        tbl_frm.pack(fill=tk.X, pady=(0, 8))

        cols = ("Estrategia", "k", "Partición", "Pérdida (φ)", "Tiempo (s)")
        self._tree = ttk.Treeview(
            tbl_frm, columns=cols,
            show="headings", height=5,
            style="Dark.Treeview",
        )
        widths = (100, 45, 320, 100, 90)
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, minwidth=w)

        vsb = ttk.Scrollbar(tbl_frm, orient=tk.VERTICAL,
                            command=self._tree.yview)
        hsb = ttk.Scrollbar(tbl_frm, orient=tk.HORIZONTAL,
                            command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(fill=tk.X)

        self._tree.tag_configure("phi_zero",
                                 background='#1a3a1a',
                                 foreground=C['phi_zero'])
        self._tree.tag_configure("phi_nonzero",
                                 foreground=C['phi_nonzero'])
        self._tree.tag_configure("timeout_row",
                                 foreground=C['text_secondary'])

        # ── Análisis Automático — Notebook con 5 pestañas ─────────────────
        anal_frm = tk.LabelFrame(
            p, text="Análisis Automático",
            font=('Segoe UI', 10, 'bold'),
            bg=C['bg_panel'], fg=C['text_primary'],
            bd=1, padx=4, pady=4,
        )
        anal_frm.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(anal_frm, style="Dark.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True)

        def _make_tab(parent, mono=True):
            frm = tk.Frame(parent, bg=C['bg_main'])
            txt = tk.Text(
                frm, wrap=tk.WORD,
                state=tk.DISABLED,
                bg=C['bg_main'], fg=C['text_primary'],
                font=('Consolas', 9 if mono else 9), relief=tk.FLAT,
                selectbackground=C['bg_hover'],
            )
            sb = tk.Scrollbar(frm, command=txt.yview, bg=C['bg_panel'])
            txt.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            txt.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            return frm, txt

        frm1, self._tab_correctitud = _make_tab(nb)
        frm2, self._tab_complejidad = _make_tab(nb)
        frm3, self._tab_eficiencia  = _make_tab(nb)
        frm4, self._tab_comparacion = _make_tab(nb)

        nb.add(frm1, text=" Correctitud ")
        nb.add(frm2, text=" Complejidad ")
        nb.add(frm3, text=" Eficiencia  ")
        nb.add(frm4, text=" Comparación ")

        # ── Pestaña 5: Datos Excel ────────────────────────────────────────
        frm5 = tk.Frame(nb, bg=C['bg_main'])

        btn_bar = tk.Frame(frm5, bg=C['bg_panel'])
        btn_bar.pack(fill=tk.X, padx=0, pady=(0, 2))

        tk.Button(
            btn_bar, text="📤 Exportar a Excel",
            command=self._exportar_a_excel,
            bg=C['accent'], fg="white",
            activebackground=C['accent_light'], activeforeground="white",
            relief=tk.FLAT, font=('Segoe UI', 9, 'bold'),
            padx=10, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=6, pady=4)

        tk.Button(
            btn_bar, text="📥 Exportar todo el historial",
            command=self._exportar_historial_excel,
            bg='#1f6feb', fg="white",
            activebackground='#388bfd', activeforeground="white",
            relief=tk.FLAT, font=('Segoe UI', 9),
            padx=8, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=4, pady=4)

        tk.Button(
            btn_bar, text="🗑 Limpiar tabla",
            command=self._limpiar_excel_tab,
            bg=C['bg_hover'], fg=C['text_secondary'],
            activebackground=C['border'], activeforeground=C['text_primary'],
            relief=tk.FLAT, font=('Segoe UI', 9),
            padx=8, pady=5,
        ).pack(side=tk.LEFT, padx=4, pady=4)

        tk.Button(
            btn_bar, text="📊 Completar plataformas",
            command=self._completar_plataformas,
            bg='#6e40c9', fg="white",
            activebackground='#8957e5', activeforeground="white",
            relief=tk.FLAT, font=('Segoe UI', 9),
            padx=8, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=4, pady=4)

        excel_txt_frm = tk.Frame(frm5, bg=C['bg_main'])
        excel_txt_frm.pack(fill=tk.BOTH, expand=True)

        self._tab_excel_txt = tk.Text(
            excel_txt_frm, wrap=tk.NONE,
            state=tk.DISABLED,
            bg=C['bg_main'], fg=C['text_primary'],
            font=('Consolas', 8), relief=tk.FLAT,
            selectbackground=C['bg_hover'],
        )
        excel_vsb = tk.Scrollbar(excel_txt_frm,
                                 command=self._tab_excel_txt.yview,
                                 bg=C['bg_panel'])
        excel_hsb = tk.Scrollbar(excel_txt_frm, orient=tk.HORIZONTAL,
                                 command=self._tab_excel_txt.xview,
                                 bg=C['bg_panel'])
        self._tab_excel_txt.configure(
            yscrollcommand=excel_vsb.set,
            xscrollcommand=excel_hsb.set)
        excel_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        excel_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tab_excel_txt.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        nb.add(frm5, text=" 📋 Datos Excel ")

    def _build_bottom(self):
        C = COLORS
        tk.Frame(self, height=1, bg=C['border']).pack(
            fill=tk.X, padx=10, pady=(6, 0))

        bar = tk.Frame(self, bg=C['bg_panel'])
        bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        self._status = tk.StringVar(value="Listo")
        tk.Label(
            bar, textvariable=self._status, anchor="w",
            width=45, bg=C['bg_panel'], fg=C['text_secondary'],
            font=('Segoe UI', 9),
        ).pack(side=tk.LEFT, padx=8, pady=6)

        self._pb = ttk.Progressbar(bar, mode="indeterminate", length=200)
        self._pb.pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(
            bar, text="💾  Guardar resultados",
            command=self._save,
            bg=C['bg_hover'], fg=C['text_primary'],
            activebackground=C['border'], activeforeground=C['text_primary'],
            relief=tk.FLAT, font=('Segoe UI', 9),
            padx=10, pady=5, cursor="hand2",
        ).pack(side=tk.RIGHT, padx=8, pady=6)

    # ── Helpers de UI (thread-safe via _q / poll) ─────────────────────────

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                kind = msg["kind"]
                if kind == "log":
                    self._log_add(msg["text"], msg.get("tag", ""))
                elif kind == "status":
                    self._status.set(msg["text"])
                elif kind == "row":
                    phi_str = msg["values"][3]
                    try:
                        phi_val = float(phi_str)
                        row_tag = "phi_zero" if phi_val < 1e-9 else "phi_nonzero"
                    except (ValueError, TypeError):
                        row_tag = "timeout_row"
                    self._tree.insert("", tk.END,
                                      values=msg["values"], tags=(row_tag,))
                    self._results.append(msg["values"])
                elif kind == "done":
                    self._on_done(msg)
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _post(self, **kw):
        self._q.put(kw)

    def _log_add(self, text: str, tag: str = ""):
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, text + "\n", tag if tag else ())
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _log_clear(self):
        self._log.configure(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.configure(state=tk.DISABLED)

    def _tab_set(self, widget, content: str):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state=tk.DISABLED)

    def _analysis_tabs_clear(self):
        """Limpia solo las 4 pestañas de análisis (preserva Excel)."""
        for w in [self._tab_correctitud, self._tab_complejidad,
                  self._tab_eficiencia,  self._tab_comparacion]:
            self._tab_set(w, "")

    def _tabs_clear(self):
        """Limpia todas las pestañas incluida Excel."""
        self._analysis_tabs_clear()
        self._tab_set(self._tab_excel_txt, "")

    def _actualizar_csv_status(self):
        path = self._csv_var.get().strip()
        if not path:
            self._csv_status_lbl.config(
                text="", fg=COLORS['text_secondary'])
            return
        self._csv_status_lbl.config(
            text="⏳ Analizando CSV…", fg=COLORS['text_secondary'])
        threading.Thread(
            target=self._analizar_csv, args=(path,), daemon=True).start()

    def _analizar_csv(self, ruta):
        if not os.path.exists(ruta):
            self.after(0, lambda: self._csv_status_lbl.config(
                text="⚠ CSV no encontrado — se usará TPM sintética",
                fg=COLORS['warning']))
            return
        try:
            n_vars  = 0
            n_filas = 0
            with open(ruta, encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    if i == 0:
                        parts = line.split(',')
                        n_vars = len(parts)
                        try:
                            float(parts[0])
                            n_filas = 1
                        except ValueError:
                            pass
                    else:
                        n_filas += 1
            esperado = 2 ** n_vars if n_vars > 0 else 0
            ok = (n_filas == esperado) and (esperado > 0)
            if ok:
                txt = (f"✓ CSV válido  —  "
                       f"{n_filas:,} estados × {n_vars} variables")
                fg  = COLORS['success']
            else:
                txt = (f"⚠ CSV cargado  —  {n_filas:,} filas "
                       f"(esperado {esperado:,})")
                fg  = COLORS['warning']
            self.after(0, lambda t=txt, c=fg: self._csv_status_lbl.config(
                text=t, fg=c))
        except Exception as e:
            msg = f"✗ Error leyendo CSV: {e}"
            self.after(0, lambda m=msg: self._csv_status_lbl.config(
                text=m, fg=COLORS['danger']))

    # ── Callbacks de widgets ───────────────────────────────────────────────

    def _on_n(self, value: str):
        if value not in PREDEFINIDOS:
            return
        self._updating_predefined = True
        cfg = PREDEFINIDOS[value]
        self._sys_var.set(cfg["sistema"])
        self._est_var.set(cfg["estado"])
        self._csv_var.set(cfg["csv"])
        self._alc_var.set(cfg["sistema"])
        self._mec_var.set(cfg["sistema"])
        self._updating_predefined = False
        self._actualizar_csv_status()

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Seleccionar CSV del sistema",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialdir="data"
        )
        if p:
            self._csv_var.set(p)

    def _clear(self):
        for v in (self._sys_var, self._est_var, self._csv_var,
                  self._alc_var, self._mec_var):
            v.set("")
        self._n_var.set("— seleccionar —")
        self._use_geo.set(True)
        self._use_qnod.set(True)
        self._log_clear()
        for it in self._tree.get_children():
            self._tree.delete(it)
        self._tabs_clear()
        self._excel_rows.clear()
        self._prueba_counter = 0
        self._historial_analisis.clear()
        self._ultimo_n_sistema = 0
        self._ultimo_sistema   = ''
        self._status.set("Listo")
        self._results.clear()
        self._actualizar_csv_status()

    def _limpiar_excel_tab(self):
        self._excel_rows.clear()
        self._prueba_counter = 0
        self._tab_set(self._tab_excel_txt, "")

    def _exportar_historial_excel(self):
        """
        Exporta TODAS las entradas del historial al Excel en un solo paso.
        Útil para guardar resultados de una suite completa o varios análisis manuales.
        """
        if not self._historial_analisis:
            messagebox.showwarning(
                "Historial vacío",
                "No hay análisis en el historial.\n"
                "Ejecuta al menos un análisis o una suite primero.")
            return

        excel_path = filedialog.askopenfilename(
            title="Selecciona DatosPruebas2026_1.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("Todos", "*.*")]
        )
        if not excel_path:
            return

        # Guardar estado actual de _ultimo_* para restaurar después
        saved_geo      = self._ultimo_res_geo
        saved_geo_full = self._ultimo_res_geo_full
        saved_qn       = self._ultimo_res_qn
        saved_sub      = self._ultimo_sub
        saved_tgeo     = self._ultimo_t_geo
        saved_tqn      = self._ultimo_t_qn
        saved_n        = self._ultimo_n_sistema

        errores = 0
        for entrada in self._historial_analisis:
            try:
                # Establecer _ultimo_* desde la entrada del historial
                self._ultimo_res_geo      = entrada['res_geo']
                self._ultimo_res_geo_full = entrada.get('res_geo_full')
                self._ultimo_res_qn       = entrada['res_qn']
                self._ultimo_sub          = entrada['sub']
                self._ultimo_t_geo        = entrada['t_geo']
                self._ultimo_t_qn         = entrada['t_qn']
                self._ultimo_n_sistema    = entrada['n_sistema']
                self._exportar_a_excel_path(
                    excel_path,
                    entrada['alcance'],
                    entrada['mecanismo'],
                    n_sistema=entrada['n_sistema'],
                )
            except Exception:
                errores += 1

        # Restaurar estado original
        self._ultimo_res_geo      = saved_geo
        self._ultimo_res_geo_full = saved_geo_full
        self._ultimo_res_qn       = saved_qn
        self._ultimo_sub          = saved_sub
        self._ultimo_t_geo        = saved_tgeo
        self._ultimo_t_qn         = saved_tqn
        self._ultimo_n_sistema    = saved_n

        total = len(self._historial_analisis)
        messagebox.showinfo(
            "Historial exportado",
            f"Exportadas {total - errores}/{total} entradas.\n"
            + (f"Errores: {errores}" if errores else "Sin errores."))

    # ── Suite de pruebas ───────────────────────────────────────────────────

    def _ejecutar_suite(self):
        from tkinter import simpledialog

        if not MODULES_OK:
            messagebox.showerror("Error",
                                 f"Módulos no disponibles:\n{MODULES_ERROR}")
            return

        opciones = list(SUITES.keys())
        eleccion = simpledialog.askstring(
            "Ejecutar suite",
            f"Escribe el nombre de la suite:\n{', '.join(opciones)}",
            initialvalue=opciones[0],
        )
        if not eleccion or eleccion not in SUITES:
            if eleccion:
                messagebox.showwarning("Suite",
                                       f"Suite no válida: {eleccion!r}")
            return

        suite = SUITES[eleccion]

        exportar_auto = messagebox.askyesno(
            "Exportar automáticamente",
            "¿Exportar cada resultado al Excel DatosPruebas2026_1.xlsx?\n"
            "(Seleccionarás el archivo Excel una sola vez)"
        )

        excel_path = None
        if exportar_auto:
            excel_path = filedialog.askopenfilename(
                title="Selecciona DatosPruebas2026_1.xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("Todos", "*.*")]
            )
            if not excel_path:
                exportar_auto = False

        self._btn_run.config(state=tk.DISABLED)
        self._btn_suite.config(state=tk.DISABLED)
        self._pb.start(10)

        pruebas = suite['pruebas']
        total   = len(pruebas)

        def _run():
            self._modo_suite_activo = True
            for idx, (alcance, mecanismo) in enumerate(pruebas, start=1):
                alc = alcance.upper()
                mec = mecanismo.upper()

                # Actualizar campos en el hilo principal (restaurar sistema + prueba)
                self.after(0, lambda a=alc, m=mec: (
                    self._sys_var.set(suite['sistema']),
                    self._est_var.set(suite['estado']),
                    self._csv_var.set(suite['csv']),
                    self._alc_var.set(a),
                    self._mec_var.set(m),
                ))

                self._post(
                    kind="status",
                    text=f"Suite {eleccion}: {idx}/{total}  {alc} × {mec}")
                self._post(
                    kind="log",
                    text=f"\n{'─'*45}\n"
                         f"  [{idx}/{total}]  alcance={alc}  mec={mec}",
                    tag="info")

                # Limpiar tabla de resultados para esta prueba
                def _reset():
                    for it in self._tree.get_children():
                        self._tree.delete(it)
                    self._results.clear()
                    self._analysis_tabs_clear()

                self.after(0, _reset)

                # Ejecutar análisis bloqueante (retorna un Event)
                done_ev = self._ejecutar_analisis_sync(
                    sistema  = suite['sistema'],
                    estado   = suite['estado'],
                    csv_path = suite['csv'],
                    alcance  = alc,
                    mec      = mec,
                )
                done_ev.wait(timeout=700)   # espera UI; max 700 s por prueba

                # Exportar al Excel si corresponde
                if exportar_auto and excel_path:
                    self._suite_prueba_actual = idx
                    self._exportar_a_excel_path(
                        excel_path, alc, mec,
                        n_sistema=len(suite['sistema']))

            self._modo_suite_activo = False
            # Restaurar GUI al terminar
            self.after(0, lambda: (
                self._btn_run.config(state=tk.NORMAL),
                self._btn_suite.config(state=tk.NORMAL),
                self._pb.stop(),
                self._status.set(
                    f"Suite '{eleccion}' completada: {total} pruebas"),
            ))

        threading.Thread(target=_run, daemon=True).start()

    # ── Ejecución ──────────────────────────────────────────────────────────

    def _run(self):
        if not MODULES_OK:
            messagebox.showerror("Error",
                                 f"Módulos no disponibles:\n{MODULES_ERROR}")
            return

        sistema  = self._sys_var.get().strip().upper()
        estado   = self._est_var.get().strip()
        csv_path = self._csv_var.get().strip()
        alcance  = self._alc_var.get().strip().upper()
        mec      = self._mec_var.get().strip().upper()

        if not all([sistema, estado, alcance, mec]):
            messagebox.showwarning(
                "Campos incompletos",
                "Completa: sistema, estado inicial, alcance y mecanismo.")
            return

        if len(estado) != len(sistema):
            messagebox.showwarning(
                "Error de configuración",
                f"El estado inicial debe tener {len(sistema)} bits "
                f"(tiene {len(estado)}).")
            return

        if not self._use_geo.get() and not self._use_qnod.get():
            messagebox.showwarning("Sin estrategias",
                                   "Selecciona al menos una estrategia.")
            return

        self._log_clear()
        for it in self._tree.get_children():
            self._tree.delete(it)
        self._analysis_tabs_clear()   # preserva la tabla Excel
        self._results.clear()
        self._btn_run.config(state=tk.DISABLED)
        self._btn_suite.config(state=tk.DISABLED)
        self._pb.start(10)
        self._status.set("Iniciando…")

        params = dict(sistema=sistema, estado=estado, csv_path=csv_path,
                      alcance=alcance, mec=mec,
                      usar_geo=self._use_geo.get(),
                      usar_qnod=self._use_qnod.get())

        threading.Thread(
            target=self._worker, kwargs=params, daemon=True).start()

    def _worker(self, sistema, estado, csv_path, alcance, mec,
                usar_geo, usar_qnod):
        import numpy as np
        t0 = time.time()
        geo_res = qnod_res = None
        sub = None

        try:
            if csv_path and os.path.exists(csv_path):
                self._post(kind="status", text="Cargando CSV…")
                self._post(kind="log",
                           text=f"📂 CSV: {csv_path}", tag="info")
                sys_full = System.desde_csv(csv_path, estado)

                # ── Corrección: estado más corto que el CSV ────────────────
                # Si tpm.shape[0] != 2^n, el estado tenía longitud incorrecta.
                # Inferir n real desde las columnas del CSV y reconstruir.
                if sys_full.tpm.shape[0] != 2 ** sys_full.n:
                    n_csv = sys_full.tpm.shape[1]
                    if n_csv > 0 and sys_full.tpm.shape[0] == 2 ** n_csv:
                        estado_csv = (estado + '0' * n_csv)[:n_csv]
                        sys_full = System.desde_csv(csv_path, estado_csv)
                        self._post(kind="log",
                                   text=f"  ⚠ Estado corregido: "
                                        f"'{estado}'→'{estado_csv}' "
                                        f"(CSV requiere n={n_csv})",
                                   tag="warn")
                    else:
                        raise ValueError(
                            f"CSV no reconocido: {sys_full.tpm.shape[0]} "
                            f"filas ≠ 2^{n_csv}={2**n_csv if n_csv>0 else '?'}")

                self._post(kind="status", text="Construyendo subsistema…")
                self._post(kind="log",
                           text=f"🔧 Subsistema: alcance={alcance}  mec={mec}",
                           tag="info")
                sub = sys_full.construir_subsistema(list(alcance), list(mec))

                # Consistencia residual de columnas (seguridad extra)
                if sub.n != sub.tpm.shape[1]:
                    cols_elim = list(range(sub.n, sub.tpm.shape[1]))
                    if cols_elim:
                        sub = sub.marginalizar_columnas(cols_elim)
                        self._post(kind="log",
                                   text=f"  ⚠ Columnas residuales corregidas: "
                                        f"tpm→{sub.tpm.shape}",
                                   tag="warn")

                # Advertencia si la forma sigue inconsistente (no bloquea)
                if sub.n > 0 and sub.tpm.shape[0] != 2 ** sub.n:
                    self._post(kind="log",
                               text=f"  ⚠ Forma inusual: "
                                    f"{sub.tpm.shape[0]} filas ≠ 2^{sub.n}",
                               tag="warn")

                # Subsistema vacío = intersección alcance∩mecanismo = ∅
                if sub.n == 0:
                    self._post(kind="log",
                               text=f"  ⚠ Alcance y mecanismo no comparten "
                                    f"variables — φ no definido (= 0).",
                               tag="warn")
                    _rv_geo = {
                        'phi': 0.0, 'k': None, 'biparticion': [[], []],
                        'tiempo': 0.0, 'nota': 'interseccion_vacia',
                        'resultados_por_k': {
                            k: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0,
                                'k': k, 'metodo': 'vacio'}
                            for k in [2, 3, 4, 5]
                        }
                    }
                    _rv_qn = {
                        'phi': 0.0, 'k': None, 'biparticion': [[], []],
                        'tiempo': 0.0, 'nota': 'interseccion_vacia',
                        'resultados_por_k': {
                            k: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0,
                                'k': k, 'metodo': 'vacio'}
                            for k in [2, 3, 4, 5]
                        },
                        'por_k': {
                            3: {'phi': 0.0, 'biparticion': [[], [], []], 'tiempo': 0.0,
                                'k': 3, 'metodo': 'vacio'},
                            4: {'phi': 0.0, 'biparticion': [[], [], [], []], 'tiempo': 0.0,
                                'k': 4, 'metodo': 'vacio'},
                            5: {'phi': 0.0, 'biparticion': [[], [], [], [], []], 'tiempo': 0.0,
                                'k': 5, 'metodo': 'vacio'},
                        }
                    }
                    for _s, _k in [("KGeoMIP", "2"), ("KQNodes", "3"),
                                   ("KQNodes", "4"), ("KQNodes", "5")]:
                        self._post(kind="row",
                                   values=(_s, _k, "∅ (sin intersección)",
                                           "0.000000", "0.000"))
                    self._post(kind="done",
                               elapsed=time.time() - t0,
                               geo=_rv_geo, qnod=_rv_qn,
                               sistema=sistema, alcance=alcance, mec=mec,
                               sub=sub)
                    return
            else:
                n_sub  = min(len(alcance), len(mec))
                n_rows = 2 ** min(n_sub, 20)
                seed   = sum(ord(c) for c in estado + alcance + mec) % (2**31)
                rng    = np.random.default_rng(seed)
                tpm    = rng.random((n_rows, n_sub))
                est_s  = (estado + "0" * n_sub)[:n_sub]
                sub    = System(tpm, est_s, list(alcance[:n_sub]))
                self._post(kind="log",
                           text=f"⚡ CSV no encontrado → subsistema sintético "
                                f"n={n_sub}, shape={sub.tpm.shape}",
                           tag="warn")

            self._post(kind="log",
                       text=f"  n={sub.n}  |  etiquetas="
                            f"{''.join(sub.etiquetas)}"
                            f"  |  tpm={sub.tpm.shape}",
                       tag="info")

            geo_res, qnod_res = self._run_strategies(
                sub, alcance, mec, usar_geo, usar_qnod)

        except Exception as exc:
            import traceback
            self._post(kind="log", text=f"\n❌ ERROR: {exc}", tag="err")
            self._post(kind="log", text=traceback.format_exc(), tag="err")
            self._post(kind="status", text=f"Error: {exc}")
            self._post(kind="done",
                       elapsed=time.time() - t0,
                       geo=None, qnod=None,
                       sistema=sistema, alcance=alcance, mec=mec,
                       sub=sub)
            return

        self._post(kind="done",
                   elapsed=time.time() - t0,
                   geo=geo_res, qnod=qnod_res,
                   sistema=sistema, alcance=alcance, mec=mec,
                   sub=sub)

    def _ejecutar_analisis_sync(self, sistema, estado, csv_path, alcance, mec,
                                usar_geo=True, usar_qnod=True):
        """
        Versión bloqueante del análisis para uso en _ejecutar_suite.

        Ejecuta en el hilo actual, posta mensajes log/status al queue,
        actualiza self._ultimo_* directamente y programa la actualización
        de UI (análisis + fila Excel) en el hilo principal vía after(0).

        Retorna un threading.Event que se activa cuando la UI ha procesado
        los resultados, permitiendo al hilo de la suite esperar antes de
        pasar a la siguiente prueba.
        """
        import numpy as np
        # Guardar N del sistema para que exportar_a_excel lo use correctamente
        self._ultimo_n_sistema = len(sistema)
        self._ultimo_sistema   = sistema
        done_event = threading.Event()
        t0 = time.time()
        geo_res = qnod_res = None
        sub = None

        try:
            if csv_path and os.path.exists(csv_path):
                if not hasattr(self, '_sistema_csv_cache'):
                    self._sistema_csv_cache = {}
                cache_key = (csv_path, estado)
                if cache_key in self._sistema_csv_cache:
                    sys_full = self._sistema_csv_cache[cache_key]
                    self._post(kind="log",
                               text=f"📂 CSV: {csv_path} (caché)", tag="info")
                else:
                    self._post(kind="status", text="Cargando CSV…")
                    self._post(kind="log",
                               text=f"📂 CSV: {csv_path}", tag="info")
                    sys_full = System.desde_csv(csv_path, estado)

                    if getattr(sys_full, '_usa_spark', False) and sys_full.tpm.shape[0] == 1:
                        pass  # Spark lazy: placeholder (1, n) correcto
                    elif sys_full.tpm.shape[0] != 2 ** sys_full.n:
                        n_csv = sys_full.tpm.shape[1]
                        if n_csv > 0 and sys_full.tpm.shape[0] == 2 ** n_csv:
                            estado_csv = (estado + '0' * n_csv)[:n_csv]
                            sys_full = System.desde_csv(csv_path, estado_csv)
                            self._post(kind="log",
                                       text=f"  ⚠ Estado corregido: "
                                            f"'{estado}'→'{estado_csv}'",
                                       tag="warn")
                        else:
                            raise ValueError(
                                f"CSV incompatible: {sys_full.tpm.shape}")
                    self._sistema_csv_cache[cache_key] = sys_full

                self._post(kind="status", text="Construyendo subsistema…")
                sub = sys_full.construir_subsistema(list(alcance), list(mec))

                # Consistencia residual de columnas
                if sub.n != sub.tpm.shape[1]:
                    cols_elim = list(range(sub.n, sub.tpm.shape[1]))
                    if cols_elim:
                        sub = sub.marginalizar_columnas(cols_elim)

                # Advertencia (no bloqueo) si forma inusual persiste
                if sub.n > 0 and sub.tpm.shape[0] != 2 ** sub.n:
                    self._post(kind="log",
                               text=f"  ⚠ Forma inusual: "
                                    f"{sub.tpm.shape[0]} filas ≠ 2^{sub.n}",
                               tag="warn")

                # Subsistema vacío = alcance∩mecanismo = ∅
                if sub.n == 0:
                    self._post(kind="log",
                               text=(f"  ⚠ Alcance ∩ Mecanismo = ∅  →  φ = 0 por definición\n"
                                     f"  (sin variables en común, no hay dependencia causal medible)"),
                               tag="warn")
                    res_geo_vacio = {
                        'phi':              0.0,
                        'k':                None,
                        'biparticion':      [[], []],
                        'tiempo':           0.0,
                        'nota':             'interseccion_vacia',
                        'resultados_por_k': {
                            2: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 2, 'metodo': 'vacio'},
                            3: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 3, 'metodo': 'vacio'},
                            4: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 4, 'metodo': 'vacio'},
                            5: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 5, 'metodo': 'vacio'},
                        }
                    }
                    res_qn_vacio = {
                        'phi':              0.0,
                        'k':                None,
                        'biparticion':      [[], []],
                        'tiempo':           0.0,
                        'nota':             'interseccion_vacia',
                        'resultados_por_k': {
                            2: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 2, 'metodo': 'vacio'},
                            3: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 3, 'metodo': 'vacio'},
                            4: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 4, 'metodo': 'vacio'},
                            5: {'phi': 0.0, 'biparticion': [[], []], 'tiempo': 0.0, 'k': 5, 'metodo': 'vacio'},
                        },
                        'por_k': {
                            3: {'phi': 0.0, 'biparticion': [[], [], []], 'tiempo': 0.0, 'k': 3, 'metodo': 'vacio'},
                            4: {'phi': 0.0, 'biparticion': [[], [], [], []], 'tiempo': 0.0, 'k': 4, 'metodo': 'vacio'},
                            5: {'phi': 0.0, 'biparticion': [[], [], [], [], []], 'tiempo': 0.0, 'k': 5, 'metodo': 'vacio'},
                        }
                    }
                    self._ultimo_res_geo      = res_geo_vacio
                    self._ultimo_res_geo_full = None   # evitar datos geo_full de prueba anterior
                    self._ultimo_res_qn       = res_qn_vacio
                    self._ultimo_sub          = sub
                    self._ultimo_t_geo        = 0.0
                    self._ultimo_t_qn         = 0.0
                    self._ultimo_n_sistema    = len(sistema)
                    _alc  = alcance
                    _mec  = mec
                    _n_sis = len(sistema)

                    def _ui_vacio():
                        self._generar_analisis(res_geo_vacio, res_qn_vacio, sub, 0.0, 0.0)
                        self._agregar_fila_excel(res_geo_vacio, res_qn_vacio, sub, _alc, _mec)
                        # Insertar filas en el Treeview con φ=0
                        for _strat, _k in [("KGeoMIP", "2"), ("KQNodes", "3"),
                                           ("KQNodes", "4"), ("KQNodes", "5")]:
                            _vals = (_strat, _k, "∅ (sin intersección)", "0.000000", "0.000")
                            self._tree.insert("", tk.END, values=_vals, tags=("phi_zero",))
                            self._results.append(_vals)
                        self._historial_analisis.append({
                            'alcance':      _alc,
                            'mecanismo':    _mec,
                            'n_sistema':    _n_sis,
                            'res_geo':      res_geo_vacio,
                            'res_geo_full': None,
                            'res_qn':       res_qn_vacio,
                            'sub':          sub,
                            't_geo':        0.0,
                            't_qn':         0.0,
                        })
                        self._post(kind="log",
                                   text="\n✅ Completado (φ = 0, intersección vacía)",
                                   tag="ok")
                        self._status.set("φ = 0 (intersección vacía)")
                        done_event.set()

                    self.after(0, _ui_vacio)
                    return done_event
            else:
                n_sub  = min(len(alcance), len(mec))
                n_rows = 2 ** min(n_sub, 20)
                seed   = sum(ord(c) for c in estado + alcance + mec) % (2**31)
                rng    = np.random.default_rng(seed)
                tpm    = rng.random((n_rows, n_sub))
                est_s  = (estado + "0" * n_sub)[:n_sub]
                sub    = System(tpm, est_s, list(alcance[:n_sub]))
                self._post(kind="log",
                           text=f"⚡ Subsistema sintético n={n_sub}",
                           tag="warn")

            self._post(kind="log",
                       text=f"  n={sub.n}  |  etiquetas="
                            f"{''.join(sub.etiquetas)}"
                            f"  |  tpm={sub.tpm.shape}",
                       tag="info")

            geo_res, qnod_res = self._run_strategies(
                sub, alcance, mec, usar_geo, usar_qnod)

            # Actualizar _ultimo_* directamente desde el hilo de análisis
            if geo_res or qnod_res:
                self._ultimo_res_geo      = geo_res
                self._ultimo_res_geo_full = geo_res if geo_res else None
                self._ultimo_res_qn       = qnod_res
                self._ultimo_sub          = sub
                self._ultimo_t_geo        = geo_res.get("tiempo", 0.0)  if geo_res  else 0.0
                self._ultimo_t_qn         = qnod_res.get("tiempo", 0.0) if qnod_res else 0.0

        except Exception as exc:
            import traceback
            self._post(kind="log", text=f"\n❌ ERROR: {exc}", tag="err")
            self._post(kind="log", text=traceback.format_exc(), tag="err")
            # Registrar en historial con resultado vacío para mantener numeración
            self._historial_analisis.append({
                'alcance':      alcance,
                'mecanismo':    mec,
                'n_sistema':    self._ultimo_n_sistema,
                'res_geo':      None,
                'res_geo_full': None,
                'res_qn':       None,
                'sub':          None,
                't_geo':        0.0,
                't_qn':         0.0,
                'error':        str(exc),
            })
            done_event.set()
            return done_event

        elapsed = time.time() - t0

        # Programar actualización de UI en el hilo principal
        _geo   = geo_res
        _qnod  = qnod_res
        _sub   = sub
        _t_geo = self._ultimo_t_geo
        _t_qn  = self._ultimo_t_qn
        _alc   = alcance
        _mec   = mec

        _n_sis = self._ultimo_n_sistema

        def _ui_update():
            if _geo or _qnod:
                self._generar_analisis(_geo, _qnod, _sub, _t_geo, _t_qn)
                self._agregar_fila_excel(_geo, _qnod, _sub, _alc, _mec)
                self._historial_analisis.append({
                    'alcance':      _alc,
                    'mecanismo':    _mec,
                    'n_sistema':    _n_sis,
                    'res_geo':      _geo,
                    'res_geo_full': _geo,
                    'res_qn':       _qnod,
                    'sub':          _sub,
                    't_geo':        _t_geo,
                    't_qn':         _t_qn,
                })
            self._post(kind="log",
                       text=f"\n✅ Completado en {elapsed:.2f}s", tag="ok")
            self._status.set(f"Completado en {elapsed:.2f}s")
            done_event.set()

        self.after(0, _ui_update)
        return done_event

    def _run_strategies(self, sub, alcance, mec, usar_geo, usar_qnod):
        n    = sub.n
        etqs = sub.etiquetas

        def label(idx_list):
            return "".join(etqs[i] for i in idx_list) if idx_list else "∅"

        def _con_timeout(fn, timeout_s=600):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(fn)
                try:
                    return fut.result(timeout=timeout_s)
                except concurrent.futures.TimeoutError:
                    return None

        geo_res = qnod_res = None

        # ── KGeoMIP k=2,3,4,5 (Branch and Bound) ────────────────────────
        if usar_geo:
            self._post(kind="status",
                       text=f"Ejecutando KGeoMIP k=2,3,4,5 (n={n})…")
            self._post(kind="log",
                       text=f"\n▶ KGeoMIP k=2,3,4,5  (n={n})", tag="ok")
            t0 = time.time()
            try:
                k_vals   = [2, 3, 4, 5] if n <= 20 else [2]
                res_full  = _con_timeout(
                    lambda: KGeoMIPKPartition(
                        sub, k_values=k_vals).aplicar_estrategia(),
                    timeout_s=600
                )
                elapsed   = time.time() - t0
                if res_full is None:
                    raise RuntimeError("KGeoMIP excedió límite de 600s")
                res_por_k = res_full.get('resultados_por_k', {})

                # Normalizar phi / n para cada k
                resultados_norm = {}
                for k_val, rk in res_por_k.items():
                    if rk and rk.get('biparticion') is not None:
                        phi_raw_k = rk.get('phi', float('inf'))
                        resultados_norm[k_val] = {
                            'phi':         phi_raw_k / n if n > 0 else 0.0,
                            'phi_raw':     phi_raw_k,
                            'biparticion': rk.get('biparticion'),
                            'tiempo':      rk.get('tiempo', elapsed),
                        }

                # k=2 para compatibilidad con el resto de la interfaz
                rk2      = resultados_norm.get(2, {})
                phi2     = rk2.get('phi', float('inf'))
                phi_raw2 = rk2.get('phi_raw', phi2)
                bip2     = rk2.get('biparticion') or [[], []]
                p1       = bip2[0] if len(bip2) > 0 else []
                p2       = bip2[1] if len(bip2) > 1 else []
                part     = f"[{label(p1)}] | [{label(p2)}]"

                self._post(kind="log",
                           text=f"  k=2: φ = {phi2:.6f}  (raw={phi_raw2:.4f})"
                                f"  t = {elapsed:.3f}s", tag="ok")
                self._post(kind="log", text=f"  Partición: {part}")
                self._post(kind="row",
                           values=("KGeoMIP", "2", part,
                                   f"{phi2:.6f}", f"{elapsed:.3f}"))

                for k_val in [3, 4, 5]:
                    rk = resultados_norm.get(k_val)
                    if not rk or rk.get('biparticion') is None:
                        continue
                    phi_k  = rk['phi']
                    parts  = rk['biparticion']
                    part_k = " | ".join(
                        "{" + label(p) + "}" for p in parts)
                    self._post(kind="row",
                               values=("KGeoMIP", f"{k_val}", part_k,
                                       f"{phi_k:.6f}", f"{elapsed:.3f}"))

                geo_res = {
                    "phi":              phi2,
                    "phi_raw":          phi_raw2,
                    "p1":               p1,
                    "p2":               p2,
                    "part":             part,
                    "biparticion":      [p1, p2],
                    "tiempo":           elapsed,
                    "resultados_por_k": resultados_norm,
                }
            except Exception as e:
                self._post(kind="log", text=f"  ❌ Error: {e}", tag="err")

        # ── KQNodes ──────────────────────────────────────────────────────
        if usar_qnod:
            self._post(kind="status",
                       text=f"Ejecutando KQNodes (n={n})…")
            self._post(kind="log",
                       text=f"\n▶ KQNodes k=3,4,5  (n={n})", tag="ok")
            t0 = time.time()
            try:
                res = _con_timeout(
                    lambda: KQNodes(sub).aplicar_estrategia(),
                    timeout_s=600
                )
                elapsed = time.time() - t0
                if res is None:
                    raise RuntimeError("KQNodes excedió límite de 600s")
                phi     = res.get("phi", float("inf"))
                k_opt   = res.get("k", "?")
                mejor   = res.get("biparticion") or []

                if mejor:
                    part_q = " | ".join(
                        "{" + label(p) + "}" for p in mejor)
                else:
                    part_q = "sin partición válida"

                self._post(kind="log",
                           text=f"  φ_opt = {phi:.6f}  k={k_opt}"
                                f"  t = {elapsed:.3f}s", tag="ok")
                self._post(kind="log", text=f"  Partición: {part_q}")

                for k_val, rk in sorted(
                        res.get("resultados_por_k", {}).items()):
                    if rk.get("biparticion") is None:
                        continue
                    phi_k  = rk["phi"]
                    part_k = " | ".join(
                        "{" + label(p) + "}" for p in rk["biparticion"])
                    self._post(kind="row",
                               values=("KQNodes", f"{k_val}",
                                       part_k, f"{phi_k:.6f}",
                                       f"{elapsed:.3f}"))

                qnod_res = {"phi": phi, "k": k_opt,
                            "mejor": mejor, "part": part_q,
                            "biparticion": mejor,
                            "tiempo": elapsed,
                            "por_k": res.get("resultados_por_k", {})}
            except Exception as e:
                self._post(kind="log", text=f"  ❌ Error: {e}", tag="err")

        return geo_res, qnod_res

    # ── Fin de ejecución ───────────────────────────────────────────────────

    def _on_done(self, msg):
        self._pb.stop()
        self._btn_run.config(state=tk.NORMAL)
        self._btn_suite.config(state=tk.NORMAL)
        elapsed = msg.get("elapsed", 0)
        self._status.set(f"Completado en {elapsed:.2f}s")
        self._post(kind="log",
                   text=f"\n✅ Análisis completado en {elapsed:.2f}s",
                   tag="ok")

        geo  = msg.get("geo")
        qnod = msg.get("qnod")
        if geo or qnod:
            sub   = msg.get("sub")
            t_geo = geo.get("tiempo", 0.0)  if geo  else 0.0
            t_qn  = qnod.get("tiempo", 0.0) if qnod else 0.0
            # Guardar referencias para exportar_a_excel
            self._ultimo_res_geo      = geo
            self._ultimo_res_geo_full = geo
            self._ultimo_res_qn       = qnod
            self._ultimo_sub          = sub
            self._ultimo_t_geo        = t_geo
            self._ultimo_t_qn         = t_qn
            # Capturar n_sistema desde el campo UI (modo manual)
            self._ultimo_n_sistema = len(self._sys_var.get().strip())
            self._ultimo_sistema   = self._sys_var.get().strip()
            alc = msg.get("alcance", "")
            mec = msg.get("mec",     "")
            self._generar_analisis(geo, qnod, sub, t_geo, t_qn)
            self._agregar_fila_excel(geo, qnod, sub, alcance=alc, mec=mec)
            self._historial_analisis.append({
                'alcance':      alc,
                'mecanismo':    mec,
                'n_sistema':    self._ultimo_n_sistema,
                'res_geo':      geo,
                'res_geo_full': geo,
                'res_qn':       qnod,
                'sub':          sub,
                't_geo':        t_geo,
                't_qn':         t_qn,
            })

    # ── Generación de análisis → 4 pestañas ───────────────────────────────

    def _generar_analisis(self, res_geo, res_qn, sub, t_geo, t_qn):
        if sub is None:
            n, etqs = 0, []
        else:
            n, etqs = sub.n, sub.etiquetas

        sep = "─" * 55

        # ── PESTAÑA 1: CORRECTITUD ────────────────────────────────────────
        L1 = []
        L1.append("■ CORRECTITUD")
        L1.append(sep)
        L1.append("Principio: una k-partición es CORRECTA si y solo si")
        L1.append("reconstituye la distribución original con φ mínimo.")
        L1.append("  φ = EMD(dist_orig, dist_particionada) / n  ∈ [0, 1]")
        L1.append("")

        if res_geo:
            phi_g = res_geo["phi"]
            biparticion = res_geo.get("biparticion") or [[], []]
            p1, p2 = biparticion
            part_g = (f"[{''.join(etqs[i] for i in p1)}]"
                      f" | [{''.join(etqs[i] for i in p2)}]")
            if phi_g < 1e-9:
                L1.append("  KGeoMIP: φ = 0  ✓  Partición perfecta.")
                L1.append(
                    f"  Las partes {part_g} son causalmente independientes.")
                L1.append(
                    "  La distribución reconstruida ES idéntica a la original.")
            else:
                L1.append(f"  KGeoMIP: φ = {phi_g:.6f}")
                L1.append(f"  Partición {part_g} introduce pérdida.")
                L1.append(
                    "  Interpretación: existe dependencia causal entre las")
                L1.append("  partes que no puede eliminarse con k=2.")
                L1.append(
                    f"  La distribución reconstruida difiere en {phi_g:.4f}"
                    " unidades de la original (escala Hamming normalizada).")

        L1.append("")
        if res_qn and res_qn.get("phi", float("inf")) < float("inf"):
            phi_q = res_qn["phi"]
            k_opt = res_qn.get("k", "?")
            if phi_q < 1e-9:
                L1.append(f"  KQNodes: φ = 0  ✓  k={k_opt}-partición perfecta.")
                L1.append(
                    f"  El sistema se descompone completamente en {k_opt}"
                    " partes independientes sin pérdida de información.")
            else:
                L1.append(f"  KQNodes: φ = {phi_q:.6f}  k={k_opt}")
                L1.append(f"  Pérdida mínima hallada con {k_opt} partes.")
        elif res_qn:
            if n < 3:
                L1.append(f"  KQNodes: no ejecutado — n={n} < 3 variables.")
                L1.append(
                    "  (se necesitan al menos 3 variables para k=3,4,5)")
            else:
                L1.append("  KQNodes: sin resultado válido (posible timeout)")

        self._tab_set(self._tab_correctitud, "\n".join(L1))

        # ── PESTAÑA 2: COMPLEJIDAD ────────────────────────────────────────
        L2 = []
        L2.append("■ COMPLEJIDAD ASINTÓTICA  (n_sub = %d)" % n)
        L2.append(sep)

        if n > 0:
            num_estados = 2 ** n
            bip_total   = 2 ** (n - 1) - 1

            L2.append("  KGeoMIP:")
            L2.append("  ├─ Tabla T (BFS sparse):")
            L2.append(
                f"  │    T(n) = n · 2^n = {n} · {num_estados}"
                f" = {n * num_estados:,} ops")
            L2.append("  │    Clase: O(n · 2^n)  —  exponencial en n")
            L2.append("  ├─ Biparticiones candidatas:")
            L2.append(
                f"  │    2^(n-1) - 1 = {bip_total:,} biparticiones posibles")
            L2.append(
                f"  │    Evaluadas: "
                f"{'exhaustivo' if n <= 15 else 'heurístico (n>15)'}")
            L2.append("  └─ Total: O(n · 2^n)")
            L2.append("")

            L2.append("  KQNodes:")
            for k in [3, 4, 5]:
                if k > n:
                    continue
                s = stirling2(n, k)
                L2.append(f"  ├─ k={k}: S({n},{k}) = {s:,} particiones")
                L2.append(
                    f"  │    Costo por partición: O(k · 2^n)"
                    f" = O({k}·{num_estados:,})")
                L2.append(
                    f"  │    Total k={k}: {s * k * num_estados:,} ops"
                    f" ~ O(S(n,{k})·n·2^n)")
            L2.append("  └─ Con memoización: reduce a O(2^n) cálculos únicos")
            L2.append("")
            L2.append("  Comparación de orden:")
            L2.append(
                f"  KGeoMIP     O(n·2^n)          ="
                f" {n * num_estados:>12,}")
            if n >= 3:
                s3 = stirling2(n, 3)
                L2.append(
                    f"  KQNodes k=3 O(S(n,3)·n·2^n) ="
                    f" {s3 * n * num_estados:>12,}")
        else:
            L2.append("  (sin datos de subsistema)")

        self._tab_set(self._tab_complejidad, "\n".join(L2))

        # ── PESTAÑA 3: EFICIENCIA ─────────────────────────────────────────
        L3 = []
        L3.append("■ EFICIENCIA")
        L3.append(sep)

        if res_geo and t_geo > 0:
            phi_g = res_geo["phi"]
            L3.append(f"  KGeoMIP:  t = {t_geo:.4f}s")
            if phi_g > 1e-9:
                L3.append(
                    f"  ├─ Rendimiento: {t_geo / phi_g:.2f} s por unidad-φ")
                L3.append(
                    f"  └─ Para φ=0 necesitaría ≈{t_geo * phi_g:.4f}s adicionales")
            else:
                L3.append(f"  └─ Óptimo: φ=0 alcanzado en {t_geo:.4f}s")

        if (res_qn and res_qn.get("phi", float("inf")) < float("inf")
                and t_qn > 0):
            phi_q = res_qn["phi"]
            L3.append(f"  KQNodes:  t = {t_qn:.4f}s")
            if phi_q > 1e-9:
                L3.append(
                    f"  ├─ Rendimiento: {t_qn / phi_q:.2f} s por unidad-φ")
            else:
                L3.append(
                    f"  └─ Óptimo: φ=0 alcanzado en {t_qn:.4f}s")

        if not res_geo and not res_qn:
            L3.append("  Sin datos para calcular eficiencia.")

        self._tab_set(self._tab_eficiencia, "\n".join(L3))

        # ── PESTAÑA 4: COMPARACIÓN ────────────────────────────────────────
        L4 = []
        L4.append("■ COMPARACIÓN ENTRE ESTRATEGIAS")
        L4.append(sep)

        phi_g = res_geo["phi"] if res_geo else float("inf")
        phi_q = (res_qn["phi"]
                 if (res_qn and
                     res_qn.get("phi", float("inf")) < float("inf"))
                 else float("inf"))

        if phi_g < float("inf") and phi_q < float("inf"):
            ganador = "KGeoMIP" if phi_g <= phi_q else "KQNodes"
            dif_phi = abs(phi_g - phi_q)
            dif_t   = abs(t_geo - t_qn)
            mas_rap = "KGeoMIP" if t_geo < t_qn else "KQNodes"

            L4.append(f"  Pérdida mínima: {ganador}")
            L4.append(f"  ├─ KGeoMIP φ = {phi_g:.6f}  (k=2)")
            L4.append(
                f"  ├─ KQNodes φ = {phi_q:.6f}  (k={res_qn.get('k','?')})")
            L4.append(f"  └─ Diferencia: Δφ = {dif_phi:.6f}")
            L4.append("")
            L4.append(f"  Velocidad: {mas_rap} más rápido por {dif_t:.4f}s")
            L4.append("")

            if res_geo and res_qn and res_qn.get("biparticion"):
                vars_g  = set(etqs[i] for i in res_geo["biparticion"][0])
                vars_q1 = set(etqs[v] for v in res_qn["biparticion"][0])
                if vars_g == vars_q1:
                    L4.append(
                        "  Concordancia: ambas estrategias identificaron")
                    L4.append(
                        "  el mismo subconjunto de variables como primera parte.")
                else:
                    L4.append(
                        "  Divergencia: cada estrategia encontró una")
                    L4.append(
                        "  estructura de partición diferente.")
                L4.append("")

            L4.append("  Recomendación:")
            if phi_g <= phi_q:
                L4.append("  → Usar KGeoMIP: menor pérdida con k=2.")
                L4.append(
                    "    Si φ>0, el sistema tiene dependencia causal")
                L4.append(
                    "    irreducible que ninguna bipartición elimina.")
            else:
                L4.append("  → Usar KQNodes: menor pérdida con k>2.")
                L4.append(
                    "    El sistema requiere más de 2 partes para")
                L4.append(
                    "    capturar su estructura causal real.")

        elif phi_g < float("inf") and phi_q == float("inf"):
            # KQNodes no completó — mostrar causa y recomendación
            L4.append("  KQNodes no completó en este subsistema.")
            L4.append("  Posibles causas:")
            L4.append(f"  ├─ Subsistema con n={n} variables y k=3,4,5")
            L4.append(f"  │   requiere S(n,3)+S(n,4)+S(n,5) evaluaciones")
            if n >= 3:
                total = sum(stirling2(n, k) for k in [3, 4, 5] if k <= n)
                L4.append(f"  │   Total: {total:,} particiones a evaluar")
            L4.append("  ├─ Timeout de 600s aplicado automáticamente")
            L4.append("  └─ Recomendación: reducir el subsistema a n≤8")
            L4.append("     para obtener comparación completa.")
            L4.append("")
            L4.append(f"  KGeoMIP disponible: φ = {phi_g:.6f}  (k=2)")

        elif phi_g < float("inf"):
            L4.append("  Solo KGeoMIP disponible para comparación.")
            L4.append(f"  KGeoMIP: φ = {phi_g:.6f}  (k=2)")
        else:
            L4.append("  Sin resultados suficientes para comparar.")

        self._tab_set(self._tab_comparacion, "\n".join(L4))

    # ── Pestaña 5: Datos Excel ────────────────────────────────────────────

    def _agregar_fila_excel(self, geo, qnod, sub, alcance, mec):
        """Añade una fila a self._excel_rows y refresca la pestaña."""
        self._prueba_counter += 1
        etqs = sub.etiquetas if sub else []

        def lbl(idxs):
            if not idxs or not etqs:
                return '—'
            return "".join(etqs[i] for i in idxs if i < len(etqs))

        # KGeoMIP k=2
        bip = geo.get('biparticion') if geo else None
        if geo and bip and len(bip) == 2:
            p1, p2 = bip
            geo_d = {
                'part': f"[{lbl(p1)}]|[{lbl(p2)}]",
                'phi':  f"{geo['phi']:.6f}",
                't':    f"{geo.get('tiempo', 0.0):.3f}",
            }
        else:
            geo_d = {'part': '—', 'phi': '—', 't': '—'}

        # KQNodes por k
        por_k   = qnod.get('por_k', {}) if qnod else {}
        t_qn    = qnod.get('tiempo', 0)  if qnod else 0
        qn_d    = {}
        for k in [3, 4, 5]:
            rk = por_k.get(k, {})
            if (rk and rk.get('biparticion') is not None
                    and rk.get('phi', float('inf')) < float('inf')):
                parts_str = " | ".join(
                    "{" + lbl(p) + "}" for p in rk['biparticion'])
                qn_d[k] = {
                    'part': parts_str,
                    'phi':  f"{rk['phi']:.6f}",
                    't':    f"{t_qn:.3f}",
                }
            else:
                qn_d[k] = {'part': '—', 'phi': '—', 't': '—'}

        # Geometric k=3,4,5
        res_geo_full = getattr(self, '_ultimo_res_geo_full', None)
        por_k_geo    = res_geo_full.get('resultados_por_k', {}) if res_geo_full else {}
        geo_kn_d     = {}
        for k in [3, 4, 5]:
            rk = por_k_geo.get(k, {})
            if (rk and rk.get('biparticion') is not None
                    and rk.get('phi', float('inf')) < float('inf')):
                parts_str = " | ".join(
                    "{" + lbl(p) + "}" for p in rk['biparticion'])
                geo_kn_d[k] = {
                    'part': parts_str,
                    'phi':  f"{rk['phi']:.6f}",
                    't':    f"{rk.get('tiempo', 0):.3f}",
                }
            else:
                geo_kn_d[k] = {'part': '—', 'phi': '—', 't': '—'}

        self._excel_rows.append({
            'prueba':  self._prueba_counter,
            'alcance': alcance,
            'mec':     mec,
            'geo':     geo_d,
            'qn':      qn_d,
            'geo_kn':  geo_kn_d,
        })
        # DEBUG temporal — eliminar después de verificar N=25 pruebas 42/48
        _r = self._excel_rows[-1]
        print(f"DEBUG _agregar_fila_excel: _excel_rows tiene {len(self._excel_rows)} entradas")
        print(f"  prueba={_r['prueba']}  alcance={_r['alcance']}  mec={_r['mec']}")
        print(f"  geo.phi={_r['geo'].get('phi','?')}  qn[3].phi={_r['qn'].get(3,{}).get('phi','?')}"
              f"  qn[4].phi={_r['qn'].get(4,{}).get('phi','?')}  qn[5].phi={_r['qn'].get(5,{}).get('phi','?')}")
        self._actualizar_tab_excel()

    def _actualizar_tab_excel(self):
        """
        Muestra preview en formato k | Estrategia | Partición | Pérdida | Tiempo.
        Una fila por combinación (KGeoMIP k=2, KQNodes k=3,4,5).
        Muestra el análisis más reciente + historial acumulado al final.
        """
        lines = []
        sep = "─" * 72

        # ── Cabecera de columnas ──────────────────────────────────────────
        lines.append(
            f"{'k':>2}  {'Estrategia':<12}  "
            f"{'Partición':<28}  {'Pérdida (φ)':>12}  {'Tiempo (s)':>10}")
        lines.append(sep)

        if not self._excel_rows:
            lines.append(
                "  (sin datos — ejecuta un análisis para agregar filas)")
            self._tab_set(self._tab_excel_txt, "\n".join(lines))
            return

        # ── Último análisis (bloque más reciente) ─────────────────────────
        r = self._excel_rows[-1]
        lines.append(
            f"  Análisis #{r['prueba']:>2}  │  "
            f"Alcance: {r['alcance']:<12}  │  Mec: {r['mec']}")
        lines.append("─" * 40)

        g = r['geo']
        if g['part'] != '—':
            lines.append(
                f"{2:>2}  {'KGeoMIP':<12}  "
                f"{g['part'][:28]:<28}  {g['phi']:>12}  {g['t']:>10}")

        for k in [3, 4, 5]:
            q = r['qn'].get(k, {'part': '—', 'phi': '—', 't': '—'})
            if q['part'] != '—':
                lines.append(
                    f"{k:>2}  {'KQNodes':<12}  "
                    f"{q['part'][:28]:<28}  {q['phi']:>12}  {q['t']:>10}")

        for k in [3, 4, 5]:
            gk = r.get('geo_kn', {}).get(k, {'part': '—', 'phi': '—', 't': '—'})
            if gk['part'] != '—':
                lines.append(
                    f"{k:>2}  {'KGeoMIP':<12}  "
                    f"{gk['part'][:28]:<28}  {gk['phi']:>12}  {gk['t']:>10}")

        # ── Historial acumulado (si hay más de un análisis) ───────────────
        if len(self._excel_rows) > 1:
            lines.append("")
            lines.append(sep)
            lines.append(
                f"  Historial: {len(self._excel_rows)} análisis listos para exportar")
            lines.append(sep)
            lines.append(
                f"{'#':>3}  {'Alcance':<12}  {'Mec':<12}  "
                f"{'Geo-k2 φ':>10}  {'QN-k3 φ':>10}  "
                f"{'QN-k4 φ':>10}  {'QN-k5 φ':>10}")
            lines.append("─" * 72)
            for hr in self._excel_rows:
                hg  = hr['geo']
                hq3 = hr['qn'].get(3, {'phi': '—'})
                hq4 = hr['qn'].get(4, {'phi': '—'})
                hq5 = hr['qn'].get(5, {'phi': '—'})
                lines.append(
                    f"{hr['prueba']:>3}  "
                    f"{hr['alcance'][:12]:<12}  {hr['mec'][:12]:<12}  "
                    f"{hg['phi']:>10}  {hq3['phi']:>10}  "
                    f"{hq4['phi']:>10}  {hq5['phi']:>10}")

        lines.append("")
        lines.append("  → Pulsa '📤 Exportar a Excel' para escribir en DatosPruebas2026_1.xlsx")

        self._tab_set(self._tab_excel_txt, "\n".join(lines))

    def _exportar_a_excel(self):
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror(
                "openpyxl no instalado",
                "Instala la dependencia:\n  pip install openpyxl\n\n"
                "Luego reinicia la interfaz.")
            return

        if self._ultimo_res_geo is None and self._ultimo_res_qn is None:
            messagebox.showinfo("Sin datos",
                                "Ejecuta un análisis antes de exportar.")
            return

        # Determinar hoja según N del sistema completo
        # Preferir _ultimo_n_sistema (válido tras análisis/suite) sobre campo UI
        n_total = self._ultimo_n_sistema
        if not n_total and hasattr(self, '_ultimo_sub') and self._ultimo_sub:
            n_total = self._ultimo_sub.n
        if not n_total:
            csv_path = self._csv_var.get().strip()
            for _suite_v in SUITES.values():
                if _suite_v.get('csv', '') and (
                    _suite_v['csv'] in csv_path or csv_path.endswith(_suite_v['csv'])
                ):
                    n_total = _suite_v.get('n_sistema', 0)
                    break
        if not n_total:
            n_total = len(self._sys_var.get().strip())
        hoja_nombre = HOJAS_EXCEL.get(n_total)
        if not hoja_nombre:
            messagebox.showwarning(
                "Excel",
                f"N={n_total} no tiene hoja en el Excel.\n"
                f"Hojas disponibles: N={list(HOJAS_EXCEL.keys())}")
            return

        # Buscar el Excel en rutas comunes
        rutas = [
            'DatosPruebas2026_1.xlsx',
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'DatosPruebas2026_1.xlsx'),
            '../DatosPruebas2026_1.xlsx',
            '../../DatosPruebas2026_1.xlsx',
        ]
        excel_path = next((r for r in rutas if os.path.exists(r)), None)
        if not excel_path:
            excel_path = filedialog.askopenfilename(
                title="Selecciona DatosPruebas2026_1.xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("Todos", "*.*")]
            )
        if not excel_path:
            return

        try:
            wb = openpyxl.load_workbook(excel_path)
            if hoja_nombre not in wb.sheetnames:
                messagebox.showwarning(
                    "Excel",
                    f"Hoja '{hoja_nombre}' no encontrada.\n"
                    f"Hojas disponibles: {', '.join(wb.sheetnames)}")
                wb.close()
                return

            ws = wb[hoja_nombre]

            alcance   = self._alc_var.get().strip().upper()
            mecanismo = self._mec_var.get().strip().upper()

            # Buscar fila por Alcance (col B=2) y Mecanismo (col C=3), desde fila 6
            fila_destino = None
            for row in ws.iter_rows(min_row=6, max_col=3, values_only=False):
                cell_alc = row[1]   # col B (índice 1)
                cell_mec = row[2]   # col C (índice 2)
                if (str(cell_alc.value or '').strip().upper() == alcance and
                        str(cell_mec.value or '').strip().upper() == mecanismo):
                    fila_destino = cell_alc.row
                    break

            if fila_destino is None:
                messagebox.showwarning(
                    "Excel",
                    f"No se encontró la combinación:\n"
                    f"  Alcance   = {alcance}\n"
                    f"  Mecanismo = {mecanismo}\n\n"
                    f"en la hoja '{hoja_nombre}'.\n"
                    f"Verifica que la fila exista con esos valores en cols B y C.")
                wb.close()
                return

            # ── Mapeo de columnas (D=4 … AA=27) ──────────────────────────
            # Col D:  QNodes k=2  Partición   Col E:  QNodes k=2  Pérdida
            # Col F:  QNodes k=2  Tiempo      Col G:  Geometric k=2  Partición
            # Col H:  Geometric k=2  Pérdida  Col I:  Geometric k=2  Tiempo
            # Col J:  QNodes k=3  Partición   Col K:  QNodes k=3  Pérdida
            # Col L:  QNodes k=3  Tiempo      Col M:  Geometric k=3  Partición
            # Col N:  Geometric k=3  Pérdida  Col O:  Geometric k=3  Tiempo
            # Col P:  QNodes k=4  Partición   Col Q:  QNodes k=4  Pérdida
            # Col R:  QNodes k=4  Tiempo      Col S:  Geometric k=4  Partición
            # Col T:  Geometric k=4  Pérdida  Col U:  Geometric k=4  Tiempo
            # Col V:  QNodes k=5  Partición   Col W:  QNodes k=5  Pérdida
            # Col X:  QNodes k=5  Tiempo      Col Y:  Geometric k=5  Partición
            # Col Z:  Geometric k=5  Pérdida  Col AA: Geometric k=5  Tiempo
            COL = {
                'qnodes_k2_part': 4,  'qnodes_k2_perd': 5,  'qnodes_k2_t': 6,
                'geo_k2_part':    7,  'geo_k2_perd':    8,  'geo_k2_t':    9,
                'qnodes_k3_part': 10, 'qnodes_k3_perd': 11, 'qnodes_k3_t': 12,
                'geo_k3_part':    13, 'geo_k3_perd':    14, 'geo_k3_t':    15,
                'qnodes_k4_part': 16, 'qnodes_k4_perd': 17, 'qnodes_k4_t': 18,
                'geo_k4_part':    19, 'geo_k4_perd':    20, 'geo_k4_t':    21,
                'qnodes_k5_part': 22, 'qnodes_k5_perd': 23, 'qnodes_k5_t': 24,
                'geo_k5_part':    25, 'geo_k5_perd':    26, 'geo_k5_t':    27,
            }

            def escribir(col_key, valor):
                if valor is not None:
                    ws.cell(row=fila_destino, column=COL[col_key], value=valor)

            etqs = self._ultimo_sub.etiquetas if self._ultimo_sub else []

            def lbl_part(idxs):
                if not idxs or not etqs:
                    return None
                return "".join(etqs[i] for i in idxs if i < len(etqs))

            # ── KGeoMIP k=2 → cols G,H,I ────────────────────────────────
            if self._ultimo_res_geo:
                rg = self._ultimo_res_geo
                p1, p2 = rg['biparticion']
                part_str = (lbl_part(p1) or '') + '|' + (lbl_part(p2) or '')
                escribir('geo_k2_part', part_str)
                escribir('geo_k2_perd', round(float(rg['phi']), 8))
                escribir('geo_k2_t',    round(float(self._ultimo_t_geo), 4))

            # ── KQNodes k=3,4,5 → cols J..X ─────────────────────────────
            if self._ultimo_res_qn:
                rq    = self._ultimo_res_qn
                por_k = rq.get('resultados_por_k', {})
                t_qn  = self._ultimo_t_qn

                for k_val in [3, 4, 5]:
                    res_k = por_k.get(k_val)
                    if not res_k or res_k.get('biparticion') is None:
                        continue
                    phi_k = res_k.get('phi', float('inf'))
                    if phi_k >= float('inf'):
                        continue
                    parts = res_k['biparticion']
                    part_str = ' | '.join(
                        '{' + (lbl_part(p) or '') + '}'
                        for p in parts
                    )
                    escribir(f'qnodes_k{k_val}_part', part_str)
                    escribir(f'qnodes_k{k_val}_perd', round(float(phi_k), 8))
                    escribir(f'qnodes_k{k_val}_t',    round(float(t_qn), 4))

            wb.save(excel_path)
            wb.close()
            messagebox.showinfo(
                "Excel exportado",
                f"✓ Datos escritos correctamente.\n\n"
                f"  Hoja  : {hoja_nombre}\n"
                f"  Fila  : {fila_destino}\n"
                f"  Archivo: {excel_path}")

        except Exception as e:
            import traceback
            messagebox.showerror(
                "Error exportando",
                f"{e}\n\n{traceback.format_exc()[:500]}")

    def _exportar_a_excel_path(self, excel_path: str, alcance: str,
                               mecanismo: str, n_sistema: int = None):
        """
        Escribe resultados en DatosPruebas2026_1.xlsx en la hoja correspondiente.

        Estructura de columnas (fila 6 en adelante, A=#Prueba, B=Alcance, C=Mecanismo):
          D-F  : QNodes  Bipartición (k=2, derivada de k=3)
          G-I  : Geometric Bipartición (k=2)
          J-L  : QNodes  3-Partición (k=3)
          M-O  : Geometric 3-Partición (k=3)  — vacío (KGeoMIP solo hace k=2)
          P-R  : QNodes  4-Partición (k=4)
          S-U  : Geometric 4-Partición (k=4)  — vacío
          V-X  : QNodes  5-Partición (k=5)
          Y-AA : Geometric 5-Partición (k=5)  — vacío
        """
        try:
            import openpyxl
        except ImportError:
            self._post(kind="log",
                       text="  ✗ openpyxl no instalado (pip install openpyxl)",
                       tag="err")
            return

        n_total = (n_sistema
                   or self._ultimo_n_sistema
                   or len(self._sys_var.get().strip()))
        hoja_nombre = HOJAS_EXCEL.get(n_total)
        if not hoja_nombre:
            self._post(kind="log",
                       text=f"  ✗ N={n_total} sin hoja Excel configurada",
                       tag="warn")
            return

        if not os.path.exists(excel_path):
            self._post(kind="log",
                       text=f"  ✗ Archivo no encontrado: {excel_path}",
                       tag="err")
            return

        try:
            wb = openpyxl.load_workbook(excel_path)

            # Buscar hoja (tolerante a espacios y guiones)
            ws = None
            for nombre_hoja in wb.sheetnames:
                if nombre_hoja.strip() == hoja_nombre.strip():
                    ws = wb[nombre_hoja]
                    hoja_nombre = nombre_hoja
                    break
            if ws is None:
                norm = hoja_nombre.lower().replace('-', '').replace(' ', '')
                hoja_alt = next(
                    (h for h in wb.sheetnames
                     if h.lower().replace('-', '').replace(' ', '') == norm),
                    None
                )
                if hoja_alt:
                    hoja_nombre = hoja_alt
                    ws = wb[hoja_nombre]
                    self._post(kind="log",
                               text=f"  Usando hoja alternativa: '{hoja_nombre}'",
                               tag="warn")
                else:
                    hojas_disp = wb.sheetnames
                    wb.close()
                    self._post(kind="log",
                               text=f"  ✗ Hoja '{hoja_nombre}' no encontrada. "
                                    f"Disponibles: {hojas_disp}",
                               tag="err")
                    return

            # Buscar fila por Alcance (col B) y Mecanismo (col C), desde fila 6
            alc_up = alcance.strip().upper()
            mec_up = mecanismo.strip().upper()
            fila_destino = None
            for row in ws.iter_rows(min_row=6, max_col=3, values_only=False):
                val_b = str(row[1].value or '').strip().upper()
                val_c = str(row[2].value or '').strip().upper()
                if val_b == alc_up and val_c == mec_up:
                    fila_destino = row[0].row
                    break

            if fila_destino is None:
                n_prueba = getattr(self, '_suite_prueba_actual', None)
                if n_prueba is not None:
                    fila_destino = 5 + n_prueba  # prueba 1 → fila 6, prueba 2 → fila 7, etc.
                    self._post(kind="log",
                               text=f"  → Fila asignada secuencialmente: {fila_destino} "
                                    f"(alcance={alc_up} mec={mec_up})",
                               tag="info")
                else:
                    self._post(kind="log",
                               text=f"  ⚠ Fila no encontrada y sin índice: "
                                    f"alcance={alc_up} mec={mec_up}",
                               tag="warn")
                    wb.close()
                    return

            etqs = self._ultimo_sub.etiquetas if self._ultimo_sub else []

            def w(col, valor):
                if valor is not None and valor != '':
                    ws.cell(row=fila_destino, column=col, value=valor)

            def fmt_part_geo(bip):
                if not bip:
                    return None
                p1, p2 = bip
                s1 = ''.join(etqs[i] for i in p1 if i < len(etqs)) if p1 else ''
                s2 = ''.join(etqs[i] for i in p2 if i < len(etqs)) if p2 else ''
                return '∅' if not s1 and not s2 else f"{s1}|{s2}"

            def fmt_part_qn(parts):
                if not parts or all(len(p) == 0 for p in parts):
                    return '∅'
                parts_strs = [
                    ''.join(etqs[v] for v in p if v < len(etqs))
                    for p in parts
                    if len(p) > 0
                ]
                if not parts_strs or all(s == '' for s in parts_strs):
                    return '∅'
                return ' | '.join('{' + s + '}' for s in parts_strs)

            res_geo = self._ultimo_res_geo
            res_qn  = self._ultimo_res_qn
            # _run_strategies almacena resultados por k bajo la clave 'por_k'
            por_k   = res_qn.get('por_k', {}) if res_qn else {}

            # Caso intersección vacía: escribir ∅ / 0.0 en todas las columnas D-AA
            _es_vacio = (res_geo and res_geo.get('nota') == 'interseccion_vacia')
            if _es_vacio:
                # cols D-AA en grupos de 3: (partición, phi, tiempo)
                for _col_ini in [4, 7, 10, 13, 16, 19, 22, 25]:
                    w(_col_ini,     '∅')
                    w(_col_ini + 1, 0.0)
                    w(_col_ini + 2, 0.0)
                try:
                    wb.save(excel_path)
                    wb.close()
                    self._post(kind="log",
                               text=f"  ✓ Excel (∅): {hoja_nombre} fila {fila_destino}",
                               tag="ok")
                except PermissionError:
                    self._post(kind="log",
                               text=f"  ✗ Excel bloqueado (¿abierto en otro programa?)",
                               tag="err")
                return

            # ── BLOQUE 1: QNodes k=2 → cols D(4), E(5), F(6) ─────────────
            # KQNodes no calcula k=2; se usa la primera parte de k=3 vs el
            # resto como bipartición implícita para rellenar la columna.
            rk3 = por_k.get(3)
            if rk3 and rk3.get('biparticion') and rk3.get('phi', float('inf')) < float('inf'):
                parts_k3 = rk3['biparticion']
                if len(parts_k3) >= 2:
                    p1_vars = parts_k3[0]
                    p2_vars = [v for p in parts_k3[1:] for v in p]
                    s1 = ''.join(etqs[v] for v in p1_vars if v < len(etqs))
                    s2 = ''.join(etqs[v] for v in p2_vars if v < len(etqs))
                    w(4, f"{s1}|{s2}")
                    w(5, round(float(rk3['phi']), 8))
                    t_qn_k2 = res_qn.get('tiempo', self._ultimo_t_qn) if res_qn else 0.0
                    w(6, round(float(t_qn_k2), 4))

            # ── BLOQUE 2: Geometric k=2 → cols G(7), H(8), I(9) ──────────
            if res_geo and res_geo.get('biparticion'):
                part_g = fmt_part_geo(res_geo['biparticion'])
                if part_g is not None:
                    w(7, part_g)
                w(8, round(float(res_geo['phi']), 8))
                w(9, round(float(self._ultimo_t_geo), 4))

            # ── BLOQUES 3-8: QNodes k=3,4,5 ──────────────────────────────
            # QNodes k=3 → J(10),K(11),L(12)
            # QNodes k=4 → P(16),Q(17),R(18)
            # QNodes k=5 → V(22),W(23),X(24)
            COL_QN = {3: 10, 4: 16, 5: 22}
            for k_val in [3, 4, 5]:
                col_qn = COL_QN[k_val]
                rk = por_k.get(k_val)
                if (rk and rk.get('biparticion') is not None
                        and rk.get('phi', float('inf')) < float('inf')):
                    part_str = fmt_part_qn(rk['biparticion'])
                    w(col_qn,     part_str)
                    w(col_qn + 1, round(float(rk['phi']), 8))
                    t_k_individual = rk.get('tiempo', 0.0)
                    if t_k_individual <= 0 and self._ultimo_t_qn > 0:
                        t_k_individual = self._ultimo_t_qn / 3
                    w(col_qn + 2, round(float(t_k_individual), 4))

            # ── BLOQUES Geometric k=3,4,5 → M(13),N(14),O(15) / S(19),T(20),U(21) / Y(25),Z(26),AA(27) ──
            res_geo_full = getattr(self, '_ultimo_res_geo_full', None)
            por_k_geo    = res_geo_full.get('resultados_por_k', {}) if res_geo_full else {}
            GEO_KN_COL   = {3: 13, 4: 19, 5: 25}
            for k_val in [3, 4, 5]:
                col_start = GEO_KN_COL[k_val]
                rk = por_k_geo.get(k_val)
                if (rk and rk.get('biparticion') is not None
                        and rk.get('phi', float('inf')) < float('inf')):
                    parts    = rk['biparticion']
                    part_str = fmt_part_qn(parts)
                    w(col_start,     part_str)
                    w(col_start + 1, round(float(rk['phi']), 8))
                    w(col_start + 2, round(float(rk.get('tiempo', 0.0)), 4))

            try:
                wb.save(excel_path)
                wb.close()
                self._post(kind="log",
                           text=f"  ✓ Excel: {hoja_nombre} fila {fila_destino}",
                           tag="ok")
            except PermissionError:
                dir_destino = os.path.dirname(os.path.abspath(excel_path))
                nombre_base = os.path.splitext(os.path.basename(excel_path))[0]
                copia_path  = os.path.join(
                    dir_destino,
                    f"{nombre_base}_KQNODES_EXPORT.xlsx"
                )
                try:
                    wb.save(copia_path)
                    wb.close()
                    self._post(kind="log",
                               text=(f"  ⚠ Excel abierto — guardado como:\n"
                                     f"    {copia_path}"),
                               tag="warn")
                except Exception as e2:
                    self._post(kind="log",
                               text=f"  ✗ No se pudo guardar copia: {e2}",
                               tag="err")
                if not getattr(self, '_modo_suite_activo', False):
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "Excel en uso",
                        f"El archivo está abierto en Excel.\n\n"
                        f"Los datos se guardaron en:\n{copia_path}\n\n"
                        f"Cierra Excel y luego copia los datos al archivo original."
                    )

        except Exception as e:
            import traceback
            self._post(kind="log",
                       text=f"  ✗ Error Excel: {e}\n{traceback.format_exc()[:300]}",
                       tag="err")

    # ── Guardar CSV ────────────────────────────────────────────────────────

    def _completar_plataformas(self):
        import platform, psutil, openpyxl, multiprocessing

        excel_path = filedialog.askopenfilename(
            title="Selecciona DatosPruebas2026_1.xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not excel_path:
            return
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb['plataformas']

            ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 0)
            so     = f"{platform.system()} {platform.release()}"
            proc   = platform.processor() or platform.machine()
            freq   = ''
            try:
                freq_info = psutil.cpu_freq()
                if freq_info:
                    freq = f"{freq_info.max / 1000:.2f} GHz"
            except Exception:
                pass
            ncpus = multiprocessing.cpu_count()

            # Columnas reales según estructura de la hoja: A3=Procesador, B3=RAM, C3=SO
            ws['A3'] = proc
            ws['B3'] = f"{int(ram_gb)} GB"
            ws['C3'] = so
            ws['B4'] = f"{freq}  {ncpus} núcleos".strip()

            wb.save(excel_path)
            wb.close()
            messagebox.showinfo(
                "Plataformas",
                f"Información del sistema escrita en hoja 'plataformas':\n"
                f"Procesador : {proc}\n"
                f"RAM        : {int(ram_gb)} GB\n"
                f"S.O.       : {so}\n"
                f"CPU        : {freq}  {ncpus} núcleos"
            )
        except Exception as e:
            messagebox.showerror("Error al completar plataformas", str(e))

    def _save(self):
        if not self._results:
            messagebox.showinfo("Sin datos", "No hay resultados para guardar.")
            return
        os.makedirs("results", exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"results/resultado_manual_{ts}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Estrategia", "k", "Partición",
                        "Pérdida (φ)", "Tiempo (s)"])
            w.writerows(self._results)
        messagebox.showinfo("Guardado", f"Resultados exportados a:\n{path}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
