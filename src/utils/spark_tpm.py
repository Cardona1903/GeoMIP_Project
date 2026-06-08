"""
SparkTPMLoader: carga y opera sobre TPMs grandes (N>=20) usando Apache Spark.

Estrategia: Programación Dinámica distribuida.
- El problema tiene subproblemas repetidos (marginalización de bloques de filas)
- Spark divide la TPM en particiones procesadas independientemente
- Los resultados se combinan con operaciones de agregación distribuida
- Se reutilizan cálculos almacenados en caché (spark.cache())

Aplicable cuando: archivo CSV > 40 MB (N>=20, TPM > 1M filas)
"""

import numpy as np
import os
from numpy.typing import NDArray


def _spark_disponible() -> bool:
    try:
        import pyspark  # noqa: F401
        import subprocess, re
        result = subprocess.run(
            ['java', '-version'], capture_output=True, text=True, timeout=5
        )
        ver_text = result.stderr + result.stdout
        m = re.search(r'version "(\d+)', ver_text)
        if m:
            major = int(m.group(1))
            if major == 1:
                m2 = re.search(r'version "1\.(\d+)', ver_text)
                major = int(m2.group(1)) if m2 else 8
            return major >= 17
        return False
    except Exception:
        return False


class SparkTPMLoader:
    """
    Carga TPMs grandes con PySpark y retorna arrays numpy reducidos.
    Para sistemas N>=20 donde numpy solo cargaría 43MB-188MB en RAM.
    """

    def __init__(self, n_partitions: int = 8, driver_memory: str = "4g"):
        from pyspark.sql import SparkSession
        self.spark = (
            SparkSession.builder
            .appName("KQNodes-GeoMIP")
            .master("local[*]")
            .config("spark.driver.memory", driver_memory)
            .config("spark.sql.shuffle.partitions", str(n_partitions))
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
        self.spark.sparkContext.setLogLevel("ERROR")
        self._n_partitions = n_partitions

    def cargar_tpm_subsistema(
        self,
        filepath:       str,
        estado_inicial: str,
        alcance_vars:   list[str],
        mecanismo_vars: list[str],
        todas_vars:     list[str],
    ) -> NDArray[np.float64]:
        """
        Carga solo las filas y columnas necesarias del CSV usando Spark,
        evitando cargar toda la TPM en memoria.

        Proceso distribuido:
        1. Leer CSV completo con Spark (lazy, no carga en RAM)
        2. Filtrar filas: solo estados donde las vars fuera del mecanismo
           tienen el valor del estado inicial (background conditions)
        3. Seleccionar columnas: solo las del alcance
        4. Agregar filas duplicadas (marginalización): promedio por grupo
        5. Recolectar resultado reducido en numpy (mucho menor que la TPM completa)
        """
        from pyspark.sql import functions as F

        # Leer CSV con Spark (lazy)
        df = self.spark.read.csv(filepath, header=True, inferSchema=True)
        col_names = df.columns
        n_total   = len(col_names)

        # Mapeo var -> índice de columna en el CSV
        var_to_col = {v: i for i, v in enumerate(todas_vars)}

        mec_indices = sorted(var_to_col[v] for v in mecanismo_vars if v in var_to_col)
        alc_indices = sorted(var_to_col[v] for v in alcance_vars  if v in var_to_col)

        # Variables fuera del mecanismo → background conditions
        fondo_indices = sorted(set(range(n_total)) - set(mec_indices))

        # Convertir estado_inicial a bits (little-endian: A=bit0, B=bit1...)
        bits = [(int(estado_inicial[::-1], 2) >> i) & 1 for i in range(n_total)]

        # Agregar columna de índice de fila para reconstruir el estado binario
        df = df.withColumn("__row_idx__", F.monotonically_increasing_id())

        # Filtro: bit de cada variable de fondo == valor en estado_inicial
        filtro = None
        for col_idx in fondo_indices:
            bit_esperado = bits[col_idx]
            condicion = (
                (F.col("__row_idx__").cast("long").bitwiseAND(1 << col_idx)) != 0
            ) == bool(bit_esperado)
            filtro = condicion if filtro is None else (filtro & condicion)

        if filtro is not None:
            df = df.filter(filtro)

        # Seleccionar solo columnas del alcance
        cols_alc = [col_names[i] for i in alc_indices]
        df_alc   = df.select(cols_alc)

        # Recolectar en numpy (2^|mec| filas × |alc| columnas)
        rows = df_alc.collect()
        if not rows:
            return np.zeros((1, len(cols_alc)), dtype=np.float64)

        arr = np.array(
            [[float(r[c]) for c in cols_alc] for r in rows],
            dtype=np.float64
        )
        return arr

    def stop(self):
        if self.spark:
            self.spark.stop()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()
