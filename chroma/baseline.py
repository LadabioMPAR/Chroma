"""Correção de linha de base de cromatogramas.

Dois métodos, portados de correct_base_linear.py e correct_baseline_beads.py:

    linear  -> ajuste de uma reta (polyfit grau 1) subtraída do sinal.
    beads   -> BEADS: linha de base suave, estimada iterativamente
               (boa para linhas de base curvas / com deriva).

Cada função devolve o vetor `baseline`; o sinal corrigido é `signal - baseline`.
"""

import numpy as np
from scipy.signal import savgol_filter


def linear_baseline(time, signal):
    """Linha de base = reta ajustada por mínimos quadrados (polyfit grau 1)."""
    coef = np.polyfit(time, signal, 1)
    return np.polyval(coef, time)


def beads_baseline(signal, lam=3e5, fc=0.01, r=0.5, nit=60):
    """BEADS — idêntico ao script original (matrizes densas).

    Parâmetros:
        lam  regularização (quanto maior, mais suave a baseline);
        fc   fração usada para a janela do savgol (janela = fc * N);
        r    escala da ponderação assimétrica;
        nit  número de iterações.

    Obs.: usa matrizes densas N×N (como o original). Para cromatogramas muito
    longos pode ficar pesado; nesse caso reduza N ou reamostre.
    """
    y = np.asarray(signal, dtype=float)
    N = len(y)
    D = np.diff(np.eye(N), 2, axis=0)
    H = lam * (D.T @ D)

    win = int(max(5, int(fc * N)))
    if win % 2 == 0:
        win += 1

    z = y.copy()
    w = np.ones(N)
    for _ in range(nit):
        W = np.diag(w)
        z = np.linalg.solve(W + H, w * y)
        z = savgol_filter(z, win, 3)
        d = y - z
        w = 1 / (1 + (d / r) ** 2)
    return z


def correct(time, signal, method="linear", **params):
    """Aplica o método escolhido e devolve (baseline, corrected).

    `method`: "linear" ou "beads". Para "beads", `**params` = lam, fc, r, nit.
    """
    if method == "linear":
        baseline = linear_baseline(time, signal)
    elif method == "beads":
        baseline = beads_baseline(signal, **params)
    else:
        raise ValueError(f"Método de baseline desconhecido: {method!r}")
    corrected = np.asarray(signal, dtype=float) - baseline
    return baseline, corrected
