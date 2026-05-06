"""
Punto de entrada principal del proyecto GeoMIP.
Ejecuta GeometricSIA paralelo para N = 3, 5, 10, 15.
"""
import numpy as np
import os
import multiprocessing
from src.models.system import System
from src.controllers.strategies.geometric import GeometricSIA
from src.utils.metrics import RegistroMetricas, Resultado


def verificar_tabla_n3(sistema: System) -> bool:
    """
    Verifica costos calculados contra la Tabla 4.2 del documento 2.

    El documento etiqueta los estados como 'abc' donde A=primer dígito.
    Internamente, la variable A es bit0 (LSB). Por lo tanto:
      doc_label 'abc' -> le_idx = a*1 + b*2 + c*4
    (mismo orden que el sistema interno, sin transformación extra)
    """
    geo = GeometricSIA(sistema)
    geo.tensores = sistema.obtener_tensores()
    geo.tabla_costos = geo._calcular_tabla_costos_paralelo()

    def doc_le(label: str) -> int:
        """Convierte label doc 'abc' a índice LE: a=bit0, b=bit1, c=bit2."""
        return int(label[0]) * 1 + int(label[1]) * 2 + int(label[2]) * 4

    # Tabla 4.2 completa del documento 2
    tabla_doc = {
        ('A','000'):0.0,    ('A','100'):0.0,    ('A','010'):0.0,
        ('A','110'):0.0,    ('A','001'):0.5,    ('A','101'):0.375,
        ('A','011'):0.375,  ('A','111'):0.21875,
        ('B','000'):0.0,    ('B','100'):0.0,    ('B','010'):0.5,
        ('B','110'):0.375,  ('B','001'):0.0,    ('B','101'):0.0,
        ('B','011'):0.375,  ('B','111'):0.21875,
        ('C','000'):0.0,    ('C','100'):0.5,    ('C','010'):0.0,
        ('C','110'):0.375,  ('C','001'):0.0,    ('C','101'):0.375,
        ('C','011'):0.0,    ('C','111'):0.21875,
    }
    # En el sistema interno (columnas invertidas al cargar):
    # col 0 = variable C (bit2 del doc = bit0 interno... no)
    # La inversión de columnas en desde_csv hace:
    #   col_interna_0 = tensor de variable A del doc (col_doc_{n-1})
    # Pero los tensores se obtienen por col interna.
    # Con columnas invertidas: tensor[0]=A_doc, tensor[1]=B_doc, tensor[2]=C_doc
    # Espera -- desde_csv hace tpm[:, ::-1], así:
    #   col_interna_0 = col_doc_{n-1} = C_doc (para n=3)
    #   col_interna_2 = col_doc_0     = A_doc
    # Entonces tensor[0]=C_doc, tensor[1]=B_doc, tensor[2]=A_doc
    # Para verificar la tabla del doc: A->tensor[2], B->tensor[1], C->tensor[0]
    var_map = {"A": 0, "B": 1, "C": 2}
    idx_inicio = 0

    print("\n  Verificacion Tabla 4.2 del documento 2:")
    print(f"  {'Transicion':<22}{'Esperado':>10}{'Calculado':>11}{'':>5}")
    print("  " + "-" * 51)

    todos_ok = True
    for (var, lbl), esp in tabla_doc.items():
        j = doc_le(lbl)
        T = geo.tabla_costos[var_map[var]]
        calc = T['fila_inicio'][j] if isinstance(T, dict) else T[idx_inicio, j]
        ok = abs(calc - esp) < 1e-4
        if not ok:
            todos_ok = False
        s = "OK" if ok else "FAIL"
        print(f"  t_{var}(000,{lbl})   {esp:>10.5f}  {calc:>10.5f}  {s}")

    return todos_ok


def ejecutar_para_n(
    n: int,
    registro: RegistroMetricas,
    carpeta: str = "data"
) -> None:
    """Ejecuta GeometricSIA paralelo para un sistema de N variables."""
    ncpus = multiprocessing.cpu_count()
    print(f"\n{'='*58}")
    print(f"  GeometricSIA (paralelo) para N={n}  [{ncpus} CPUs]")
    print(f"{'='*58}")

    estado = "0" * n
    csv_path = os.path.join(carpeta, f"N{n}C.csv")

    if not os.path.exists(csv_path):
        print(f"  AVISO: {csv_path} no encontrado.")
        return

    print(f"  Cargando: {csv_path}")
    sistema = System.desde_csv(csv_path, estado)
    print(f"  {sistema}")

    # Verificación especial para N=3 (caso de estudio del documento)
    if n == 3:
        ok = verificar_tabla_n3(sistema)
        print(f"\n  Tabla 4.2: {'CORRECTO ✓' if ok else 'INCORRECTO ✗'}")

    # Ejecutar algoritmo
    estrategia = GeometricSIA(sistema)
    resultado = estrategia.ejecutar()
    estrategia.imprimir_resultado()

    registro.registrar(Resultado(
        n=n,
        estado_inicial=estado,
        biparticion=resultado['biparticion'],
        phi=resultado['phi'],
        tiempo=resultado['tiempo'],
        estrategia="GeometricSIA-Paralelo"
    ))


def main():
    ncpus = multiprocessing.cpu_count()
    print("\n" + "=" * 58)
    print("  PROYECTO GeoMIP - Algoritmo Geometrico Paralelo")
    print("  Analisis y Diseno de Algoritmos 2025C")
    print(f"  CPUs disponibles: {ncpus}")
    print("=" * 58)

    registro = RegistroMetricas(carpeta="results")

    # N=20 eliminado: escala de memoria/tiempo prohibitiva
    for n in [3, 5, 10, 15]:
        try:
            ejecutar_para_n(n, registro)
        except MemoryError:
            print(f"  ERROR N={n}: Memoria insuficiente.")
        except Exception as e:
            print(f"  ERROR N={n}: {e}")
            import traceback
            traceback.print_exc()

    registro.resumen()
    registro.guardar_csv("resultados_geomip.csv")
    print("\n  Archivos de resultados guardados en: results/")


if __name__ == "__main__":
    main()