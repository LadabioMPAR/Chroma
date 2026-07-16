"""Ajuste global dos padrões — estima k e theta compartilhados.

Mesma matemática de `trava_teta_k_.py`: um único `least_squares` ajusta,
simultaneamente, um k e um theta comuns a TODOS os cromatogramas, mais um par
(A, mu) para cada pico de cada cromatograma. O vetor de parâmetros é:

    [k, theta, A_1, mu_1, A_2, mu_2, ...]

Observação: este ajuste é específico do modelo `gamma` (é ele que tem os
parâmetros de forma k e theta a serem travados depois). Está escrito chamando
`model.function(t, A, mu, k, theta)` para manter a estrutura, mas o passo 03
usa `gamma`.
"""

import numpy as np
from scipy.optimize import least_squares

from .models import get_model


def _residuals(params, all_t, all_y, n_peaks_list, model):
    k, theta = params[0], params[1]
    idx = 2
    res = []
    for t, y_exp, n_peaks in zip(all_t, all_y, n_peaks_list):
        y_pred = np.zeros_like(t)
        for _ in range(n_peaks):
            A = params[idx]
            mu = params[idx + 1]
            y_pred += model.function(t, A, mu, k, theta)
            idx += 2
        res.append(y_pred - y_exp)
    return np.concatenate(res)


def fit_global_shared_ktheta(
    all_t,
    all_y,
    peaks_list,
    model_name="gamma",
    k0=5.0,
    theta0=0.2,
    verbose=2,
):
    """Ajuste global com k e theta compartilhados.

    Args:
        all_t, all_y: listas de vetores (tempo, sinal), um par por cromatograma.
        peaks_list:   lista de arrays de índices de pico (um array por cromatograma).
        k0, theta0:   chutes iniciais dos parâmetros compartilhados.

    Devolve:
        result         -> objeto do scipy.optimize.least_squares
        n_peaks_list   -> nº de picos usado em cada cromatograma
        k, theta       -> valores estimados (result.x[0], result.x[1])
    """
    model = get_model(model_name)

    params0 = [k0, theta0]
    n_peaks_list = []
    for t, y, peaks in zip(all_t, all_y, peaks_list):
        n_peaks_list.append(len(peaks))
        for pk in peaks:
            params0 += [y[pk], t[pk]]   # A0, mu0

    result = least_squares(
        _residuals,
        params0,
        args=(all_t, all_y, n_peaks_list, model),
        bounds=(0, np.inf),
        verbose=verbose,
    )

    return result, n_peaks_list, float(result.x[0]), float(result.x[1])
