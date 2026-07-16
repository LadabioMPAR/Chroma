"""Detecção de picos.

Dois presets, correspondentes às duas estratégias usadas nos scripts
originais — mantidos separados de propósito, pois têm semântica diferente:

    prominence       -> find_peaks(prominence=..., distance=...)
                        (analise_gamma.py e analise travado.py)
    relative_height  -> find_peaks(height=max(y)*height_rel, distance=...)
                        (trava_teta_k_.py; com fallback para argmax)
"""

import numpy as np
from scipy.signal import find_peaks


def detect_prominence(signal, prominence=0.1, distance=1):
    peaks, _ = find_peaks(signal, prominence=prominence, distance=distance)
    return peaks


def detect_relative_height(signal, height_rel=0.1, distance=5, fallback_argmax=True):
    thr = np.max(signal) * height_rel
    peaks, _ = find_peaks(signal, height=thr, distance=distance)
    if len(peaks) == 0 and fallback_argmax:
        peaks = np.array([int(np.argmax(signal))])
    return peaks


def detect(signal, cfg):
    """Detecta picos a partir de um bloco de config [*.peaks].

    Espera uma chave `method` ("prominence" ou "relative_height") e os
    parâmetros correspondentes.
    """
    method = cfg.get("method", "prominence")
    if method == "prominence":
        return detect_prominence(
            signal,
            prominence=cfg.get("prominence", 0.1),
            distance=cfg.get("distance", 1),
        )
    if method == "relative_height":
        return detect_relative_height(
            signal,
            height_rel=cfg.get("height_rel", 0.1),
            distance=cfg.get("distance", 5),
        )
    raise ValueError(f"Método de detecção de picos desconhecido: {method!r}")
