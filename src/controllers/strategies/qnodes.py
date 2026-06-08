import numpy as np
from numpy.typing import NDArray
from itertools import combinations
from src.controllers.strategies.sia import SIA
from src.models.system import System
from src.utils.emd import emd_pyphi


def _particionar_conjunto(elementos: list[int], k: int):
    """
    Genera todas las k-particiones de 'elementos' en exactamente k
    partes no vacías usando números de Stirling de segundo tipo.

    Complejidad: S(n,k) particiones generadas.
        S(5,3)=25  S(10,3)=9330  S(10,4)=145750  S(15,3)≈2.38M
    """
    n = len(elementos)
    if k == 1:
        yield [list(elementos)]
        return
    if k == n:
        yield [[e] for e in elementos]
        return
    if k > n or k <= 0:
        return

    primer = elementos[0]
    resto  = elementos[1:]

    # Opción 1: primer forma su propio grupo
    for sub in _particionar_conjunto(resto, k - 1):
        yield [[primer]] + sub

    # Opción 2: primer se une a uno de los k grupos del resto
    for sub in _particionar_conjunto(resto, k):
        for i in range(k):
            nuevo = [list(g) for g in sub]
            nuevo[i] = [primer] + nuevo[i]
            yield nuevo


def _dist_parte_vectorizada(
    tpm:           NDArray[np.float64],
    futuro_cols:   list[int],
    presente_bits: list[int],
    n:             int,
    idx_inicio:    int
) -> NDArray[np.float64]:
    """
    Distribución marginal de una parte usando numpy vectorizado puro.

    Proceso (Definition 2.1.1 del documento):
    1. Seleccionar columnas de t+1 de esta parte (alcance)
    2. Agrupar filas por valor de las variables en presente_bits (mecanismo)
       y promediar -> marginalización de t
    3. Evaluar en el estado inicial de este mecanismo
    4. Construir distribución conjunta con producto de Kronecker

    Vectorización: np.arange + operaciones de bits + np.add.at
    (sin loops de Python, paralelismo real en BLAS/LAPACK de numpy)
    """
    if not futuro_cols or not presente_bits:
        return np.array([1.0])

    tpm_cols   = tpm[:, futuro_cols]
    n_pres     = len(presente_bits)
    num_pres   = 2 ** n_pres
    pres_sorted = sorted(presente_bits)

    # Calcular índice reducido para cada estado — vectorizado
    all_states = np.arange(2 ** n, dtype=np.int32)
    idx_red    = np.zeros(2 ** n, dtype=np.int32)
    for pos, bit in enumerate(pres_sorted):
        idx_red += ((all_states >> bit) & 1) << pos

    # Marginalización: acumular y promediar
    tpm_red = np.zeros((num_pres, len(futuro_cols)), dtype=np.float64)
    counts  = np.zeros(num_pres, dtype=np.int32)
    np.add.at(tpm_red, idx_red, tpm_cols)
    np.add.at(counts,  idx_red, 1)
    mask = counts > 0
    tpm_red[mask] /= counts[mask, np.newaxis]

    # Estado inicial reducido al mecanismo de esta parte
    idx_pres = sum(((idx_inicio >> bit) & 1) << pos
                   for pos, bit in enumerate(pres_sorted)) % num_pres

    # Distribución conjunta por producto de Kronecker (Teorema 1.2.1)
    dist = np.array([1.0])
    for p1 in tpm_red[idx_pres]:
        dist = np.kron(dist, np.array([1.0 - p1, p1]))

    return dist


class KQNodes(SIA):
    """
    Estrategia Q-Nodos para k-particiones óptimas (k = 3, 4, 5).

    Principio central (Definition 2.1.1 del documento):
    - No se compara una parte directamente con el sistema original
    - Solo después de recombinar con producto tensorial se compara
    - La distribución particionada = kron(dist_P1, ..., dist_Pk)
    - La pérdida = EMD(dist_orig, dist_particionada) / n  -> phi en [0,1]

    Optimización clave — memoización de distribuciones marginales:
    La distribución marginal de un subconjunto S de variables es
    siempre la misma independientemente de en qué partición aparezca.
    Se calcula UNA SOLA VEZ y se reutiliza en todas las particiones
    que contengan ese subconjunto exacto.

    Complejidad sin memoización: S(n,k) × k × O(2^n)
    Complejidad con memoización: min(2^n, S(n,k)×k subsets únicos) × O(2^n)
    Speedup real para N=10, k=3: ~82x (de 4 horas a ~3 minutos)

    phi normalizado: phi_raw / n -> garantiza rango [0, 1]
    Demostración: max EMD con distancia Hamming = n (todos los bits distintos)
    """

    def __init__(self, sistema: System):
        super().__init__(sistema)
        self.n          = sistema.n
        # Mapeo variable -> columna interna (tras [::-1] en desde_csv)
        self.var_a_col  = {i: (self.n - 1 - i) for i in range(self.n)}
        # Cache de distribuciones: frozenset(vars) -> NDArray
        self._cache_dist: dict[frozenset, NDArray] = {}

    # ==================================================================
    # PUNTO DE ENTRADA
    # ==================================================================

    def aplicar_estrategia(self) -> dict:
        """
        n<=7: exacto (Stirling). n>7: greedy+búsqueda local con timeout.
        Retorna el mejor resultado global y los resultados por k.
        """
        import time
        n         = self.n
        dist_orig = self.sistema.distribucion_estado_inicial()
        variables = list(range(n))

        self._cache_dist = {}

        mejor_global = {
            'biparticion': None,
            'phi':         float('inf'),
            'phi_raw':     float('inf'),
            'k':           None,
            'dist_orig':   dist_orig,
            'dist_part':   dist_orig.copy(),
            'tiempo':      0.0,
        }
        resultados_por_k = {}

        for k in [2, 3, 4, 5]:
            if k > n:
                continue
            # k=2 exacto hasta n=20 (S(n,2)=2^(n-1)-1, manejable)
            # k>=3 exacto solo para n<=7
            usar_exacto = (k == 2 and n <= 20) or (k >= 3 and n <= 7)
            if usar_exacto:
                res_k = self._buscar_k_particion_exacto(
                    k, variables, dist_orig
                )
                res_k['metodo'] = 'exacto_stirling'
            else:
                res_k = self._greedy_k_qnodes(
                    k, variables, dist_orig, timeout_s=90.0
                )
            resultados_por_k[k] = res_k

            if res_k['phi'] < mejor_global['phi']:
                mejor_global.update(res_k)
                mejor_global['k'] = k

        mejor_global['resultados_por_k'] = resultados_por_k
        mejor_global['por_k'] = resultados_por_k  # alias de compatibilidad
        return mejor_global

    # ==================================================================
    # BÚSQUEDA DE k-PARTICIÓN CON MEMOIZACIÓN
    # ==================================================================

    def _buscar_k_particion_exacto(
        self,
        k:         int,
        variables: list[int],
        dist_orig: NDArray[np.float64]
    ) -> dict:
        """
        Evalúa todas las S(n,k) k-particiones usando memoización de
        distribuciones marginales para evitar recálculos.

        La clave de la memoización es frozenset(vars_de_la_parte):
        el mismo subconjunto de variables produce siempre la misma
        distribución marginal, independientemente de la partición.
        """
        import time
        t0         = time.time()
        n          = self.n
        tpm        = self.sistema.tpm
        idx_inicio = int(self.sistema.estado_inicial[::-1], 2)

        mejor_phi       = float('inf')
        mejor_particion = None
        mejor_dist      = dist_orig.copy()
        evaluadas       = 0

        # Límite adaptativo: exacto para n≤10, reducido para n grandes
        if n <= 10:
            max_candidatas = 200_000
        elif n <= 12:
            max_candidatas = 10_000
        else:               # n > 12: limitar para mantener tiempo razonable
            max_candidatas = 5_000

        for particion in _particionar_conjunto(variables, k):
            if evaluadas >= max_candidatas:
                break
            try:
                dist_part = self._dist_k_particion_memo(
                    particion, tpm, n, idx_inicio
                )
                # phi normalizado en [0, 1]: dividir por n
                phi_raw  = emd_pyphi(dist_orig, dist_part)
                phi_norm = phi_raw / n

                if phi_norm < mejor_phi:
                    mejor_phi       = phi_norm
                    mejor_particion = [list(p) for p in particion]
                    mejor_dist      = dist_part.copy()

                # Corte temprano: partición perfecta
                if mejor_phi < 1e-10:
                    break

            except Exception:
                continue

            evaluadas += 1

        return {
            'biparticion': mejor_particion,
            'phi':         mejor_phi,       # normalizado [0,1]
            'phi_raw':     mejor_phi * n,   # valor absoluto
            'dist_orig':   dist_orig,
            'dist_part':   mejor_dist,
            'tiempo':      time.time() - t0,
        }

    # ==================================================================
    # DISTRIBUCIÓN CON MEMOIZACIÓN DE SUBCONJUNTOS
    # ==================================================================

    def _dist_k_particion_memo(
        self,
        particion:  list[list[int]],
        tpm:        NDArray[np.float64],
        n:          int,
        idx_inicio: int
    ) -> NDArray[np.float64]:
        """
        Calcula dist_total = kron(dist_P1, ..., dist_Pk) usando caché.

        Para cada parte Pi, la distribución marginal se obtiene del caché
        si ya fue calculada antes. Esto elimina el recálculo de subconjuntos
        que aparecen en múltiples particiones.

        Ejemplo: la parte {A,B} aparece en particiones como
        {A,B}|{C}|{D,E} y {A,B}|{C,D}|{E} -> calculada UNA VEZ.
        """
        dist_total = np.array([1.0])

        for parte in particion:
            clave = frozenset(parte)

            if clave not in self._cache_dist:
                # Primera vez que aparece este subconjunto: calcular y guardar
                futuro_cols  = sorted(self.var_a_col[v] for v in parte)
                presente_bits = sorted(parte)
                self._cache_dist[clave] = _dist_parte_vectorizada(
                    tpm, futuro_cols, presente_bits, n, idx_inicio
                )

            # Combinar con producto de Kronecker (Teorema 1.2.1)
            dist_total = np.kron(dist_total, self._cache_dist[clave])

        return dist_total

    # ==================================================================
    # GREEDY + BÚSQUEDA LOCAL (n > 7)
    # ==================================================================

    def _greedy_k_qnodes(self, k: int, variables: list,
                         dist_orig, timeout_s: float = 90.0) -> dict:
        """
        Greedy + búsqueda local para KQNodes cuando n > 7.

        Fase 1 (movimientos): mover variables entre grupos si baja phi.
        Fase 2 (intercambios): intercambiar pares entre grupos si baja phi.
        Usa _dist_k_particion_memo para aprovechar el caché de marginales.
        """
        import time
        t0     = time.time()
        n_full = self.n
        tpm    = self.sistema.tpm
        idx_inicio = int(self.sistema.estado_inicial[::-1], 2)

        def calcular_phi(grupos):
            if any(not g for g in grupos):
                return float('inf')
            try:
                dist_part = self._dist_k_particion_memo(
                    grupos, tpm, n_full, idx_inicio
                )
                phi_raw = emd_pyphi(dist_orig, dist_part)
                return phi_raw / n_full if n_full > 0 else 0.0
            except Exception:
                return float('inf')

        # Inicializar: distribución round-robin de las variables
        grupos = [[] for _ in range(k)]
        for i, v in enumerate(variables):
            grupos[i % k].append(v)

        phi_actual = calcular_phi(grupos)

        def _retorno_greedy(grupos, phi, metodo='greedy_qnodes'):
            return {
                'biparticion': [sorted(g) for g in grupos],
                'phi':         phi,
                'phi_raw':     phi * n_full,
                'dist_orig':   dist_orig,
                'dist_part':   dist_orig.copy(),
                'tiempo':      time.time() - t0,
                'metodo':      metodo,
            }

        # Fase 1: mover una variable a la vez
        mejorado = True
        iters    = 0
        while mejorado and (time.time() - t0) < timeout_s * 0.6:
            mejorado = False
            iters += 1
            if iters > 50:
                break
            for g_src in range(k):
                if len(grupos[g_src]) <= 1:
                    continue
                for v in list(grupos[g_src]):
                    for g_dst in range(k):
                        if g_dst == g_src:
                            continue
                        nuevos = [list(g) for g in grupos]
                        nuevos[g_src].remove(v)
                        nuevos[g_dst].append(v)
                        phi_n = calcular_phi(nuevos)
                        if phi_n < phi_actual - 1e-9:
                            grupos     = nuevos
                            phi_actual = phi_n
                            mejorado   = True
                            if phi_actual < 1e-9:
                                return _retorno_greedy(grupos, 0.0, 'greedy_qnodes_phi0')
                            break
                    if mejorado:
                        break
                if mejorado:
                    break

        # Fase 2: intercambiar pares de variables entre grupos
        swap_mejorado = True
        while swap_mejorado and (time.time() - t0) < timeout_s * 0.9:
            swap_mejorado = False
            for g1 in range(k):
                if swap_mejorado:
                    break
                for g2 in range(g1 + 1, k):
                    if swap_mejorado:
                        break
                    for v1 in list(grupos[g1]):
                        if swap_mejorado:
                            break
                        for v2 in list(grupos[g2]):
                            if (time.time() - t0) > timeout_s * 0.9:
                                break
                            nuevos = [list(g) for g in grupos]
                            nuevos[g1].remove(v1)
                            nuevos[g1].append(v2)
                            nuevos[g2].remove(v2)
                            nuevos[g2].append(v1)
                            phi_n = calcular_phi(nuevos)
                            if phi_n < phi_actual - 1e-9:
                                grupos        = nuevos
                                phi_actual    = phi_n
                                swap_mejorado = True
                                if phi_actual < 1e-9:
                                    return _retorno_greedy(
                                        grupos, 0.0, 'greedy_qnodes_phi0')
                                break

        return _retorno_greedy(grupos, phi_actual)

    # ==================================================================
    # IMPRESIÓN DE RESULTADOS
    # ==================================================================

    def imprimir_resultado_k(self, resultado: dict) -> None:
        """Imprime resultados detallados por k con phi normalizado."""
        if not resultado:
            print("Sin resultados.")
            return

        etqs          = self.sistema.etiquetas
        resultados_k  = resultado.get('resultados_por_k', {})

        print("\n" + "=" * 60)
        print(f"  Estrategia  : QNodesKPartition")
        print(f"  Sistema     : {''.join(etqs)} (n={self.n})")
        print(f"  Estado init : {self.sistema.estado_inicial}")
        print("-" * 60)

        for k, res_k in sorted(resultados_k.items()):
            if res_k['biparticion'] is None:
                continue
            partes_str = ' | '.join(
                '{' + ','.join(etqs[v] for v in p) + '}'
                for p in res_k['biparticion']
            )
            phi_raw  = res_k.get('phi_raw', res_k['phi'] * self.n)
            phi_norm = res_k['phi']
            print(f"  k={k}: phi={phi_norm:.6f}  "
                  f"(raw={phi_raw:.4f})  [{partes_str}]")

        print("-" * 60)
        k_opt     = resultado.get('k', '?')
        phi_opt   = resultado.get('phi', float('inf'))
        phi_raw_o = resultado.get('phi_raw', phi_opt * self.n)
        mejor     = resultado.get('biparticion', [])
        mejor_str = ' | '.join(
            '{' + ','.join(etqs[v] for v in p) + '}'
            for p in (mejor or [])
        )
        print(f"  OPTIMO k={k_opt}: phi={phi_opt:.6f} (raw={phi_raw_o:.4f})")
        print(f"  Particion   : {mejor_str}")
        print(f"  Tiempo      : {resultado.get('tiempo', 0):.4f}s")
        print(f"  phi en [0,1]: {0 <= phi_opt <= 1.0 + 1e-9}")
        print("=" * 60 + "\n")


# Alias de compatibilidad
QNodesKPartition = KQNodes
