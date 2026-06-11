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

        # Para archivos >1 GB (N>=25): float16 chunked tiene prioridad sobre Spark.
        # SparkTPMLoader usa monotonically_increasing_id() que no produce índices
        # secuenciales en distribuciones multi-partición → subsistemas incorrectos.
        # Los valores 0/1 de la TPM son exactos en float16 (no hay pérdida de precisión);
        # los cálculos internos (np.bincount) hacen upcast a float64.
        if size_mb > 1000:
            import time as _time
            try:
                # Leer header para obtener n
                import csv as _csv
                with open(filepath, encoding='utf-8') as _fh:
                    _hdr = next(_csv.reader(_fh))
                try:
                    [float(x) for x in _hdr]
                    n = len(_hdr)
                except ValueError:
                    n = len(_hdr)

                N_rows  = 2 ** n
                ram_gb  = N_rows * n * 2 / 1e9  # float16 bytes
                print(f"  [Numpy16] Pre-allocating {N_rows:,} × {n} float16 ({ram_gb:.1f} GB)…")
                t_load  = _time.time()
                tpm_doc = np.empty((N_rows, n), dtype=np.float16)

                row_start = 0
                for _chunk in pd.read_csv(filepath, header=0,
                                           chunksize=2**18, low_memory=False):
                    _arr = _chunk.values.astype(np.float16)
                    _sz  = len(_arr)
                    tpm_doc[row_start:row_start + _sz] = _arr
                    row_start += _sz

                tpm16 = tpm_doc[:, ::-1].copy()
                del tpm_doc
                etqs = [chr(ord('A') + i) for i in range(n)]
                print(f"  [Numpy16] Listo: {tpm16.shape} float16 "
                      f"({tpm16.nbytes/1e9:.1f} GB) en {_time.time()-t_load:.0f}s")
                return cls(tpm16, estado_inicial, etqs)
            except MemoryError:
                print(f"  [Numpy16] OOM — usando carga chunked por subsistema")

            # Fallback: stub con carga chunked por subsistema (lento, pero funciona)
            import csv as _csv
            with open(filepath, encoding='utf-8') as f:
                primera_fila = next(_csv.reader(f))
            try:
                [float(x) for x in primera_fila]
                n = len(primera_fila)
            except ValueError:
                n = len(primera_fila)
            etqs = [chr(ord('A') + i) for i in range(n)]
            tpm_placeholder = np.zeros((1, n), dtype=np.float64)
            sistema = cls(tpm_placeholder, estado_inicial, etqs)
            sistema._chunked_path = filepath
            sistema._usa_chunked  = True
            print(f"  [Chunked] Sistema N={n} registrado ({size_mb:.0f}MB, lazy)")
            return sistema

        # Para archivos medianos (N>=20, 40–1000 MB): PySpark con indices reales.
        # No se usa para >1000 MB por el bug de monotonically_increasing_id().
        if size_mb > 40:
            try:
                from src.utils.spark_tpm import SparkTPMLoader, _spark_disponible
                if _spark_disponible():
                    print(f"  [Spark] Cargando {filepath} ({size_mb:.0f}MB) con PySpark...")
                    import csv as _csv
                    with open(filepath, encoding='utf-8') as f:
                        primera_fila = next(_csv.reader(f))
                    try:
                        [float(x) for x in primera_fila]
                        n = len(primera_fila)
                    except ValueError:
                        n = len(primera_fila)
                    etqs = [chr(ord('A') + i) for i in range(n)]
                    tpm_placeholder = np.zeros((1, n), dtype=np.float64)
                    sistema = cls(tpm_placeholder, estado_inicial, etqs)
                    sistema._spark_path    = filepath
                    sistema._usa_spark     = True
                    sistema._spark_size_mb = size_mb
                    print(f"  [Spark] Sistema N={n} registrado (TPM carga lazy)")
                    return sistema
                else:
                    print(f"  [Spark] No disponible (Java < 17), cargando con numpy...")
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
        if self.num_estados > 2 ** 16:
            # Vectorizado: evita bucle Python de O(num_estados) iteraciones
            all_s  = np.arange(self.num_estados, dtype=np.int64)
            mascara = np.ones(self.num_estados, dtype=bool)
            for idx, val in zip(indices_externos, valores):
                mascara &= ((all_s >> idx) & 1) == val
        else:
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
        n_n  = len(vars_r)
        num_n = 2 ** n_n
        tpm_n = np.zeros((num_n, self.tpm.shape[1]), dtype=np.float64)

        if self.num_estados > 2 ** 16:
            # Vectorizado con np.bincount
            all_s   = np.arange(self.num_estados, dtype=np.int64)
            idx_r_v = np.zeros(self.num_estados, dtype=np.int32)
            for p, v in enumerate(vars_r):
                idx_r_v += ((all_s >> v) & 1).astype(np.int32) << p
            cnt = np.bincount(idx_r_v, minlength=num_n)
            safe = np.maximum(cnt, 1)
            for j in range(self.tpm.shape[1]):
                tpm_n[:, j] = (
                    np.bincount(idx_r_v,
                                weights=self.tpm[:, j].astype(np.float64),
                                minlength=num_n)
                    / safe
                )
        else:
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
        # Ruta chunked para sistemas muy grandes (N>=25 sin Spark)
        if getattr(self, '_usa_chunked', False):
            try:
                return self._construir_subsistema_chunked(alcance_vars, mecanismo_vars)
            except MemoryError as e:
                print(f"  [Chunked] {e} — subsistema demasiado grande, omitiendo")
                raise
            except Exception as e:
                print(f"  [Chunked] Error ({e}), reintentando con numpy")
                self._usa_chunked = False
                if not hasattr(self, '_sistema_numpy_cache'):
                    self._sistema_numpy_cache = System._desde_csv_numpy(
                        self._chunked_path, self.estado_inicial
                    )
                return self._sistema_numpy_cache.construir_subsistema(
                    alcance_vars, mecanismo_vars
                )

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

    def _construir_subsistema_chunked(
        self,
        alcance_vars:   list[str],
        mecanismo_vars: list[str]
    ) -> "System":
        """
        Construye el subsistema leyendo el CSV en bloques (chunks) sin cargar la
        TPM completa en memoria. Eficiente para N>=25 donde la TPM completa
        (~6 GB) no cabe en RAM.

        Convención de columnas: CSV col i = X{i}t+1 = variable de índice i.
        La inversión [::-1] al final reproduce la convención interna de desde_csv.

        Limitación: levanta MemoryError si |mec| > 22 (acumuladores > ~3 GB).
        """
        import pandas as pd

        n     = self.n
        etqs  = self.etiquetas
        fp    = self._chunked_path

        var_to_idx = {v: i for i, v in enumerate(etqs)}
        alc_set    = set(alcance_vars)
        mec_set    = set(mecanismo_vars)

        # Intersección alcance ∩ mecanismo → variables del subsistema resultado
        alc_mec_indices = sorted(var_to_idx[v] for v in alc_set & mec_set if v in var_to_idx)
        mec_indices     = sorted(var_to_idx[v] for v in mec_set if v in var_to_idx)
        fondo_indices   = [i for i in range(n) if etqs[i] not in mec_set]

        n_sub = len(alc_mec_indices)
        if n_sub == 0:
            return System(np.zeros((1, 1), dtype=np.float64), '0', [etqs[0]])

        n_mec = len(mec_indices)
        if n_mec > 22:
            raise MemoryError(
                f"|mec|={n_mec} > 22: acumuladores ({2**n_mec * n_sub * 8 / 1e9:.1f} GB) "
                "exceden RAM disponible"
            )

        num_sub    = 2 ** n_sub
        idx_inicio = int(self.estado_inicial[::-1], 2)

        # Máscara de fondo para filtrado rápido: (state & bg_mask) == bg_expected
        bg_mask     = int(sum(1 << i for i in fondo_indices))
        bg_expected = int(idx_inicio & bg_mask)

        # Acumuladores indexados por estado (alc ∩ mec)
        tpm_sum = np.zeros((num_sub, n_sub), dtype=np.float64)
        tpm_cnt = np.zeros(num_sub, dtype=np.int64)

        row_start = 0
        for chunk_df in pd.read_csv(fp, header=0, chunksize=2**18,
                                    dtype=np.float32, low_memory=False):
            chunk_size = len(chunk_df)
            states = np.arange(row_start, row_start + chunk_size, dtype=np.int64)

            # Filtro de fondo
            if bg_mask:
                keep     = (states & bg_mask) == bg_expected
                states_f = states[keep]
                arr      = chunk_df.values[keep]
            else:
                states_f = states
                arr      = chunk_df.values

            row_start += chunk_size
            if len(states_f) == 0:
                continue

            # Índice de estado (alc ∩ mec) para cada fila filtrada
            sub_idx = np.zeros(len(states_f), dtype=np.int32)
            for pos, v_idx in enumerate(alc_mec_indices):
                sub_idx += ((states_f >> v_idx) & 1).astype(np.int32) << pos

            # Valores de las columnas del alcance ∩ mecanismo
            vals = arr[:, alc_mec_indices].astype(np.float64)

            np.add.at(tpm_sum, sub_idx, vals)
            np.add.at(tpm_cnt, sub_idx, 1)

        # Normalizar y aplicar inversión de columnas (igual que _desde_csv_numpy)
        safe_cnt = np.maximum(tpm_cnt[:, np.newaxis], 1)
        tpm_sub  = (tpm_sum / safe_cnt)[:, ::-1]

        nuevo_estado = ''.join(self.estado_inicial[i] for i in alc_mec_indices)
        etqs_sub     = [etqs[i] for i in alc_mec_indices]

        return System(tpm_sub, nuevo_estado, etqs_sub)

    def __repr__(self) -> str:
        return (f"System(n={self.n}, estado='{self.estado_inicial}', "
                f"etiquetas={self.etiquetas}, tpm_shape={self.tpm.shape})")
