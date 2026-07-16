"""Ajuste individual: cada pico é ajustado separadamente numa janela local.

É a mesma lógica dos scripts `analise_gamma.py` e `analise travado.py`:
para cada pico detectado, recorta-se uma janela de ± extra_window * dt em
volta dele e faz-se um `curve_fit` do modelo escolhido.

Dois modos, controlados por `fixed`:
    fixed = None                      -> ajuste LIVRE (todos os parâmetros)   [passo 02]
    fixed = {"k": ..., "theta": ...}  -> ajuste TRAVADO (fixa k e theta,      [passo 04]
                                          ajusta só o restante, p.ex. A e t0)

A área de cada pico é integrada numericamente (np.trapezoid) sobre todo o
vetor de tempo — exatamente como no script original.
"""

import numpy as np
from scipy.optimize import curve_fit

from .models import get_model


def fit_peaks_individual(
    time,
    signal,
    peak_indices,
    model_name="gamma",
    extra_window=10,
    fixed=None,
    guess_opts=None,
):
    """Ajusta cada pico individualmente.

    Devolve uma lista de dicts (um por pico), cada um com:
        peak_index, peak_time, params (dict nome->valor), curve (np.array
        do pico sobre todo o tempo), area, R2, success.
    """
    model = get_model(model_name)
    names = model.param_names
    fixed = dict(fixed or {})
    guess_opts = dict(guess_opts or {})

    dt = time[1] - time[0]
    results = []

    for idx in peak_indices:
        peak_time = time[idx]

        # Janela local de ajuste (± extra_window * dt)
        t_start = max(time[0], peak_time - extra_window * dt)
        t_end = min(time[-1], peak_time + extra_window * dt)
        mask = (time >= t_start) & (time <= t_end)
        t_peak = time[mask]
        y_peak = signal[mask]

        guess = model.initial_guess(peak_time, signal[idx], dt, **guess_opts)
        bnds = model.bounds(guess)

        free = [n for n in names if n not in fixed]
        p0 = [guess[n] for n in free]
        lower = [bnds[n][0] for n in free]
        upper = [bnds[n][1] for n in free]

        # Função com os parâmetros fixos injetados; curve_fit só otimiza os livres.
        def f(t, *free_vals):
            allp = dict(zip(free, free_vals))
            allp.update(fixed)
            return model.function(t, *[allp[n] for n in names])

        try:
            popt, _ = curve_fit(f, t_peak, y_peak, p0=p0, bounds=(lower, upper))

            allp = dict(zip(free, popt))
            allp.update(fixed)
            params = {n: float(allp[n]) for n in names}

            curve_full = model.function(time, *[params[n] for n in names])

            fit_local = model.function(t_peak, *[params[n] for n in names])
            ss_res = np.sum((y_peak - fit_local) ** 2)
            ss_tot = np.sum((y_peak - np.mean(y_peak)) ** 2)
            r2 = 1 - ss_res / ss_tot

            area = float(np.trapezoid(curve_full, time))

            results.append({
                "peak_index": int(idx),
                "peak_time": float(peak_time),
                "params": params,
                "curve": curve_full,
                "area": area,
                "R2": float(r2),
                "success": True,
            })

        except Exception as exc:  # ajuste falhou: registra NaN, como no original
            results.append({
                "peak_index": int(idx),
                "peak_time": float(peak_time),
                "params": {n: np.nan for n in names},
                "curve": np.zeros_like(time),
                "area": np.nan,
                "R2": np.nan,
                "success": False,
                "error": str(exc),
            })

    return results
