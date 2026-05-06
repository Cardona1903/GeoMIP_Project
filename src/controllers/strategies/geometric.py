import numpy as np
from numpy.typing import NDArray
from itertools import combinations
from multiprocessing import Pool, cpu_count
from src.controllers.strategies.sia import SIA
from src.models.system import System
from src.utils.emd import emd_pyphi


# ============================================================
# Funciones a nivel de módulo (requerido por multiprocessing)
# ============================================================

def _calcular_tensor_paralelo(args):
    """
    Calcula la tabla de costos para UNA variable usando BFS vectorizado.
    Está al nivel de módulo para ser serializable por multiprocessing.

    args = (var_idx, tensor_list, n, idx_inicio, modo_sparse)
    """
    var_idx, tensor_list, n, idx_inicio, modo_sparse = args
    tensor = np.array(tensor_list, dtype=np.float64)
    num_estados = 2 ** n

    def bfs_desde(i):
        """BFS vectorizado desde estado i por niveles de Hamming."""
        costos = np.zeros(num_estados, dtype=np.float64)
        # Nivel 1
        for bit in range(n):
            j = i ^ (1 << bit)
            costos[j] = 0.5 * abs(tensor[i] - tensor[j])
        # Niveles 2..n
        for d in range(2, n + 1):
            gamma = 2.0 ** (-d)
            for bits in combinations(range(n), d):
                mask = 0
                for b in bits:
                    mask |= (1 << b)
                j = i ^ mask
                diff = abs(tensor[i] - tensor[j])
                suma = sum(costos[j ^ (1 << b)] for b in bits)
                costos[j] = gamma * (diff + suma)
        return costos

    if modo_sparse:
        # Solo calcular desde el estado inicial (sparse)
        fila = bfs_desde(idx_inicio)
        return var_idx, {'fila_inicio': fila, 'idx_inicio': idx_inicio}
    else:
        # Tabla densa: calcular todas las filas
        T = np.zeros((num_estados, num_estados), dtype=np.float64)
        for i in range(num_estados):
            T[i] = bfs_desde(i)
        return var_idx, T


class GeometricSIA(SIA):
    """
    Estrategia geométrica PARALELA para encontrar la bipartición óptima.

    Implementa el algoritmo del documento 2 (GeoMIP) con:
    1. BFS vectorizado por niveles de Hamming (sin recursión)
    2. Tabla sparse para N > 8: solo fila del estado inicial
    3. Paralelización real con multiprocessing.Pool
       - Un proceso por variable (tensor)
       - Speedup: ~min(N, CPUs) veces más rápido
    4. EMD sparse: solo estados con probabilidad > 0
    5. Heurística para N > 15: reduce candidatas de O(2^n) a O(n^2)

    Sistemas soportados: N = 3, 5, 10, 15
    """

    def __init__(self, sistema: System):
        super().__init__(sistema)
        self.tabla_costos: dict = {}
        self.tensores: list = []
        self.n_workers = max(1, cpu_count() - 1)

    # ==================================================================
    # PUNTO DE ENTRADA
    # ==================================================================

    def aplicar_estrategia(self) -> dict:
        n = self.sistema.n

        # Paso 1: tensores elementales
        self.tensores = self.sistema.obtener_tensores()

        # Paso 2: tabla de costos (paralela)
        self.tabla_costos = self._calcular_tabla_costos_paralelo()

        # Paso 3: distribución original
        dist_orig = self.sistema.distribucion_estado_inicial()

        # Paso 4: biparticiones candidatas
        candidatas = self._identificar_candidatas()

        # Paso 5: evaluar candidatas con EMD
        mejor_phi = float('inf')
        mejor_biparticion = (list(range(n // 2)), list(range(n // 2, n)))
        mejor_dist_part = dist_orig.copy()

        for (p1f, p1p, p2f, p2p) in candidatas:
            try:
                dist_part = self._distribucion_particionada(
                    p1f, p1p, p2f, p2p
                )
                phi = emd_pyphi(dist_orig, dist_part)
                if phi < mejor_phi:
                    mejor_phi = phi
                    mejor_biparticion = (
                        sorted(set(p1f + p1p)),
                        sorted(set(p2f + p2p))
                    )
                    mejor_dist_part = dist_part
                if mejor_phi < 1e-10:
                    break
            except Exception:
                continue

        return {
            'biparticion': mejor_biparticion,
            'phi': mejor_phi,
            'dist_orig': dist_orig,
            'dist_part': mejor_dist_part,
            'tiempo': 0.0
        }

    # ==================================================================
    # TABLA DE COSTOS - PARALELA
    # ==================================================================

    def _calcular_tabla_costos_paralelo(self) -> dict:
        """
        Calcula la tabla T para cada variable en PARALELO.

        Diseño:
        - N <= 8 : tabla densa en memoria (num_estados × num_estados)
        - N > 8  : solo fila del estado inicial (sparse)

        Uso de memoria resultante:
            N=3:  3 × 8 × 8 × 8B     =  1.5 KB  (densa)
            N=5:  5 × 32B × 8B        =  1.3 KB  (sparse)
            N=10: 10 × 1024 × 8B      = 80 KB    (sparse)
            N=15: 15 × 32768 × 8B     = 3.8 MB   (sparse)

        Paralelización:
        - Cada tensor se procesa en un proceso independiente
        - Speedup teórico: min(N, CPUs) × speedup_secuencial
        """
        n = self.sistema.n
        idx_inicio = int(self.sistema.estado_inicial[::-1], 2)
        modo_sparse = n > 8

        args_list = [
            (var_idx, tensor.tolist(), n, idx_inicio, modo_sparse)
            for var_idx, tensor in enumerate(self.tensores)
        ]

        tabla = {}
        usar_paralelo = n >= 5 and self.n_workers > 1

        if usar_paralelo:
            try:
                with Pool(processes=min(self.n_workers, n)) as pool:
                    resultados = pool.map(
                        _calcular_tensor_paralelo, args_list
                    )
                for var_idx, T in resultados:
                    tabla[var_idx] = T
            except Exception:
                # Fallback secuencial si Pool falla
                for args in args_list:
                    var_idx, T = _calcular_tensor_paralelo(args)
                    tabla[var_idx] = T
        else:
            for args in args_list:
                var_idx, T = _calcular_tensor_paralelo(args)
                tabla[var_idx] = T

        return tabla

    # ==================================================================
    # IDENTIFICAR CANDIDATAS
    # ==================================================================

    def _identificar_candidatas(self) -> list:
        """
        Genera biparticiones candidatas a evaluar.

        Estrategia 1 (todos los N):
            Costos cero en la tabla T revelan independencia causal.

        Estrategia 2 (N <= 15):
            Todas las biparticiones posibles: C(n,1)+...+C(n,n-1)/2

        Estrategia 3 (N > 15):
            Heurística ordenada por suma de costos.
        """
        n = self.sistema.n
        indices = list(range(n))
        candidatas = []
        vistas = set()
        idx_inicio = int(self.sistema.estado_inicial[::-1], 2)

        # Obtener fila del estado inicial por variable
        filas = {}
        for v, T in self.tabla_costos.items():
            filas[v] = T['fila_inicio'] if isinstance(T, dict) else T[idx_inicio]

        # Estrategia 1: costos cero como guía
        for v, fila in filas.items():
            for j, costo in enumerate(fila):
                if costo < 1e-10 and j != idx_inicio:
                    xor = idx_inicio ^ j
                    bits = sorted([b for b in range(n) if (xor >> b) & 1])
                    rest = sorted([i for i in indices if i not in bits])
                    if bits and rest:
                        clave = (tuple(bits), tuple(rest))
                        if clave not in vistas:
                            vistas.add(clave)
                            candidatas.append((bits, bits, rest, rest))

        if n <= 15:
            # Estrategia 2: exhaustiva
            for tam in range(1, n):
                for combo in combinations(indices, tam):
                    p1 = sorted(combo)
                    p2 = sorted([i for i in indices if i not in p1])
                    clave = (tuple(p1), tuple(p2))
                    if clave not in vistas and (tuple(p2), tuple(p1)) not in vistas:
                        vistas.add(clave)
                        candidatas.append((p1, p1, p2, p2))
        else:
            # Estrategia 3: heurística
            costos_var = sorted([(filas[v].sum(), v) for v in range(n)])
            vars_ord = [v for _, v in costos_var]
            for _, var in costos_var:
                p1 = [var]
                p2 = [i for i in indices if i != var]
                clave = (tuple(p1), tuple(p2))
                if clave not in vistas:
                    vistas.add(clave)
                    candidatas.append((p1, p1, p2, p2))
            for tam in range(1, n // 2 + 1):
                p1 = sorted(vars_ord[:tam])
                p2 = sorted(vars_ord[tam:])
                clave = (tuple(p1), tuple(p2))
                if clave not in vistas:
                    vistas.add(clave)
                    candidatas.append((p1, p1, p2, p2))

        return candidatas

    # ==================================================================
    # DISTRIBUCIÓN PARTICIONADA
    # ==================================================================

    def _distribucion_particionada(
        self, p1f, p1p, p2f, p2p
    ) -> NDArray[np.float64]:
        """
        Calcula P(sistema_partido | estado_inicial) = dist1 ⊗ dist2.

        Para cada parte: marginaliza filas (variables ausentes del mecanismo)
        y selecciona columnas (variables del alcance). Luego combina con
        producto tensorial de Kronecker.
        """
        n = self.sistema.n
        tpm = self.sistema.tpm
        estado = self.sistema.estado_inicial

        def dist_parte(futuro: list, presente: list) -> NDArray:
            if not futuro or not presente:
                return np.array([1.0])
            cols = sorted(j for j in range(n) if j in futuro)
            tpm_cols = tpm[:, cols]
            pres = sorted(presente)
            n_p = len(pres)
            num_p = 2 ** n_p
            tpm_r = np.zeros((num_p, len(cols)), dtype=np.float64)
            cnt = np.zeros(num_p, dtype=np.int64)
            for s in range(2 ** n):
                ir = sum(((s >> v) & 1) << p for p, v in enumerate(pres))
                if 0 <= ir < num_p:
                    tpm_r[ir] += tpm_cols[s]
                    cnt[ir] += 1
            for i in range(num_p):
                if cnt[i] > 0:
                    tpm_r[i] /= cnt[i]
            est_r = ''.join(estado[v] for v in pres)
            idx = int(est_r[::-1], 2) % num_p
            dist = np.array([1.0])
            for p in tpm_r[idx]:
                dist = np.kron(dist, np.array([1.0 - p, p]))
            return dist

        return np.kron(dist_parte(p1f, p1p), dist_parte(p2f, p2p))
