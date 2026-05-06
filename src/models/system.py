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
        self.n = len(estado_inicial)
        self.num_estados = 2 ** self.n
        self.etiquetas = etiquetas or [
            chr(ord('A') + i) for i in range(self.n)
        ]

    @classmethod
    def desde_csv(cls, filepath: str, estado_inicial: str) -> "System":
        """
        Carga la TPM desde CSV aplicando corrección de orden de columnas.

        El documento etiqueta las columnas como At+1, Bt+1, Ct+1
        pero la columna 0 del CSV corresponde internamente a la variable
        de mayor índice (C para n=3). Se invierte el orden de columnas
        para que la columna i corresponda a la variable i (bit i).
        """
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
        # Esto corrige que el doc usa A=col0 pero internamente A=col{n-1}
        tpm = tpm_doc[:, ::-1].copy()

        etiquetas = [chr(ord('A') + i) for i in range(n)]
        return cls(tpm, estado_inicial, etiquetas)

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
        etqs = [self.etiquetas[j] for j in cols]
        return System(self.tpm[:, cols], self.estado_inicial, etqs)

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
