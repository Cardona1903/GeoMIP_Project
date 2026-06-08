import numpy as np
import pandas as pd
from numpy.typing import NDArray


class System:
    """
    Representa el sistema con su TPM y estado inicial.

    Convención interna: variable_0=bit0 (LSB), ..., variable_{n-1}=bit{n-1}.
    Los CSVs del documento etiquetan los estados como 'abc' donde A=primer
    dígito, pero internamente usan C=bit0. El método desde_csv() corrige
    esto invirtiendo el orden de columnas (A↔C) al cargar.
    """

    def __init__(
        self,
        tpm: NDArray[np.float64],
        estado_inicial: str,
        etiquetas: list[str] | None = None
    ):
        self.tpm = tpm.copy()
        self.estado_inicial = estado_inicial
        self.etiquetas = etiquetas if etiquetas is not None else [
            chr(ord('A') + i) for i in range(len(estado_inicial))
        ]
        self.n = len(self.etiquetas)
        self.num_estados = 2 ** self.n

    @classmethod
    def _desde_csv_numpy(cls, filepath: str, estado_inicial: str) -> "System":
        """Carga TPM con pandas/numpy. Usado para N<=19 o como fallback de Spark."""
        df = pd.read_csv(filepath, header=None, low_memory=False)

        # Detectar y saltar encabezado de texto si existe
        try:
            df.iloc[0].astype(float)
        except (ValueError, TypeError):
            df = df.iloc[1:].reset_index(drop=True)

        tpm_doc = df.values.astype(np.float64)
        n = len(estado_inicial)

        # Si es formato estado-estado (2^n x 2^n), convertir a estado-nodo
        if tpm_doc.shape[0] == 2**n and tpm_doc.shape[1] == 2**n:
            tpm_doc = cls._ee_a_nodo(tpm_doc, n)

        # Invertir orden de columnas: col_doc_0 -> col_interna_{n-1}, etc.
        tpm = tpm_doc[:, ::-1].copy()

        etiquetas = [chr(ord('A') + i) for i in range(n)]
        return cls(tpm, estado_inicial, etiquetas)

    @classmethod
    def desde_csv(cls, filepath: str, estado_inicial: str) -> "System":
        """
        Carga la TPM desde CSV aplicando corrección de orden de columnas.

        El documento etiqueta las columnas como At+1, Bt+1, Ct+1
        pero la columna 0 del CSV corresponde internamente a la variable
        de mayor índice (C para n=3). Se invierte el orden de columnas
        para que la columna i corresponda a la variable i (bit i).

        Para archivos > 40 MB (N>=20), intenta PySpark automáticamente;
        si PySpark no está disponible, carga con numpy con advertencia.
        """
        import os
        size_mb = os.path.getsize(filepath) / 1e6 if os.path.exists(filepath) else 0

        if size_mb > 40:
            try:
                from src.utils.spark_tpm import SparkTPMLoader, _spark_disponible
                if _spark_disponible():
                    print(f"  [Spark] Cargando {filepath} ({size_mb:.0f}MB) con PySpark...")
                    import csv as _csv
                    with open(filepath, encoding='utf-8') as f:
                        primera_fila = next(_csv.reader(f))
                    # Detectar si la primera fila es texto (encabezado) o datos
                    try:
                        [float(x) for x in primera_fila]
                        n = len(primera_fila)
                    except ValueError:
                        # Es encabezado de texto — contar columnas
                        n = len(primera_fila)
                    etqs = [chr(ord('A') + i) for i in range(n)]
                    tpm_placeholder = np.zeros((1, n), dtype=np.float64)
                    sistema = cls(tpm_placeholder, estado_inicial, etqs)
                    sistema._spark_path    = filepath
                    sistema._usa_spark     = True
                    sistema._spark_size_mb = size_mb
                    print(f"  [Spark] Sistema N={n} registrado (TPM carga lazy)")
                    return sistema
            except Exception as e:
                print(f"  [Spark] No disponible ({e}), usando numpy")

        return cls._desde_csv_numpy(filepath, estado_inicial)

    @staticmethod
    def _ee_a_nodo(tpm_ee: NDArray, n: int) -> NDArray:
        """Convierte TPM estado-estado a estado-nodo."""
        num_s = 2 ** n
        tpm_nodo = np.zeros((num_s, n), dtype=np.float64)
        for j in range(n):
            for s in range(num_s):
                for ns in range(num_s):
                    if (ns >> j) & 1:
                        tpm_nodo[s, j] += tpm_ee[s, ns]
        return tpm_nodo

    def condicionar(
        self,
        indices_externos: list[int],
        valores: list[int]
    ) -> "System":
        """Condiciona la TPM fijando variables externas a sus valores actuales."""
        mascara = np.ones(self.num_estados, dtype=bool)
        for idx, val in zip(indices_externos, valores):
            for s in range(self.num_estados):
                if ((s >> idx) & 1) != val:
                    mascara[s] = False
        tpm_f = self.tpm[mascara, :]
        cols = [j for j in range(self.n) if j not in indices_externos]
        nuevo_estado = ''.join(
            self.estado_inicial[i] for i in range(self.n)
            if i not in indices_externos
        )
        etqs = [self.etiquetas[i] for i in range(self.n)
                if i not in indices_externos]
        return System(tpm_f[:, cols], nuevo_estado, etqs)

    def marginalizar_filas(self, indices_elim: list[int]) -> "System":
        """Marginaliza eliminando variables del tiempo t (filas)."""
        vars_r = [i for i in range(self.n) if i not in indices_elim]
        n_n = len(vars_r)
        num_n = 2 ** n_n
        tpm_n = np.zeros((num_n, self.tpm.shape[1]), dtype=np.float64)
        cnt = np.zeros(num_n, dtype=int)
        for s in range(self.num_estados):
            idx_r = sum(((s >> v) & 1) << p for p, v in enumerate(vars_r))
            tpm_n[idx_r] += self.tpm[s]
            cnt[idx_r] += 1
        for i in range(num_n):
            if cnt[i] > 0:
                tpm_n[i] /= cnt[i]
        nuevo_estado = ''.join(self.estado_inicial[i] for i in vars_r)
        etqs = [self.etiquetas[i] for i in vars_r]
        return System(tpm_n, nuevo_estado, etqs)

    def marginalizar_columnas(self, indices_elim: list[int]) -> "System":
        """Marginaliza eliminando variables del tiempo t+1 (columnas)."""
        cols = [j for j in range(self.n) if j not in indices_elim]
        etqs      = [self.etiquetas[j] for j in cols]
        tpm_nueva = self.tpm[:, cols]
        # n se recalcula desde las etiquetas reales, no desde las filas
        return System(tpm_nueva, self.estado_inicial, etqs)

    def construir_subsistema(
        self,
        alcance_vars: list[str],
        mecanismo_vars: list[str]
    ) -> "System":
        """
        Construye el subsistema para un alcance y mecanismo dados.

        alcance_vars  : variables en t+1 ej. ['A','B','C']
        mecanismo_vars: variables en t   ej. ['A','B']

        Proceso:
        1. Variables fuera del mecanismo -> condicionar al valor del estado inicial
        1.5 Variables en el mecanismo pero fuera del alcance -> marginalizar filas
            (sus estados se promedian; esto ocurre cuando mec ⊃ alc)
        2. Variables fuera del alcance   -> marginalizar columnas (descartar)
            Incluye columnas huérfanas generadas por el paso 1.5.

        Para N>=20 con Spark: delega la construcción al SparkTPMLoader.
        """
        # Ruta Spark para sistemas grandes (N>=20)
        if getattr(self, '_usa_spark', False):
            try:
                from src.utils.spark_tpm import SparkTPMLoader
                with SparkTPMLoader() as loader:
                    tpm_sub = loader.cargar_tpm_subsistema(
                        filepath       = self._spark_path,
                        estado_inicial = self.estado_inicial,
                        alcance_vars   = alcance_vars,
                        mecanismo_vars = mecanismo_vars,
                        todas_vars     = self.etiquetas,
                    )
                etqs_sub = [v for v in self.etiquetas if v in alcance_vars]
                return System(tpm_sub, self.estado_inicial, etqs_sub)
            except Exception as e:
                self._usa_spark = False  # no reintentar Spark en llamadas sucesivas
                print(f"  [Spark] Error en subsistema ({e}), recargando con numpy")
                if not hasattr(self, '_sistema_numpy_cache'):
                    self._sistema_numpy_cache = System._desde_csv_numpy(
                        self._spark_path, self.estado_inicial
                    )
                    self.tpm = self._sistema_numpy_cache.tpm
                return self._sistema_numpy_cache.construir_subsistema(
                    alcance_vars, mecanismo_vars
                )

        # Paso 1: condicionar variables fuera del mecanismo
        fuera_mec_indices = [
            i for i, etq in enumerate(self.etiquetas)
            if etq not in mecanismo_vars
        ]

        if fuera_mec_indices:
            valores = [
                (int(self.estado_inicial[::-1], 2) >> i) & 1
                for i in fuera_mec_indices
            ]
            sistema_cond = self.condicionar(fuera_mec_indices, valores)
        else:
            sistema_cond = self

        # Paso 1.5: marginalizar FILAS de variables que están en el mecanismo
        # pero NO en el alcance.  Esto ocurre cuando mec ⊃ alc: las variables
        # extra del mecanismo se promedian (no condicionan) para que el número
        # de filas coincida con 2^|alcance ∩ mec|.
        mec_no_alc = [
            i for i, etq in enumerate(sistema_cond.etiquetas)
            if etq not in alcance_vars
        ]
        if mec_no_alc:
            sistema_cond = sistema_cond.marginalizar_filas(mec_no_alc)

        # Paso 2: descartar columnas cuya etiqueta NO está en alcance_vars,
        # más las columnas huérfanas que quedaron del paso 1.5
        # (marginalizar_filas reduce filas pero no las columnas correspondientes).
        fuera_alc_col = [
            i for i, etq in enumerate(sistema_cond.etiquetas)
            if etq not in alcance_vars
        ]
        cols_huerfanas = list(range(len(sistema_cond.etiquetas),
                                    sistema_cond.tpm.shape[1]))
        todas_extra = sorted(set(fuera_alc_col + cols_huerfanas))

        if todas_extra:
            sistema_final = sistema_cond.marginalizar_columnas(todas_extra)
        else:
            sistema_final = sistema_cond

        return sistema_final

    def obtener_tensores(self) -> list[NDArray[np.float64]]:
        """Retorna n tensores elementales: uno por variable futura."""
        return [self.tpm[:, j].copy() for j in range(self.n)]

    def distribucion_estado_inicial(self) -> NDArray[np.float64]:
        """Distribución conjunta P(X_t+1 | estado_inicial) por producto tensorial."""
        idx = int(self.estado_inicial[::-1], 2) % self.num_estados
        dist = np.array([1.0])
        for p1 in self.tpm[idx]:
            dist = np.kron(dist, np.array([1.0 - p1, p1]))
        return dist

    def __repr__(self) -> str:
        return (f"System(n={self.n}, estado='{self.estado_inicial}', "
                f"etiquetas={self.etiquetas}, tpm_shape={self.tpm.shape})")
