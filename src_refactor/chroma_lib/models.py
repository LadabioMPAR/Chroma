import numpy as np
from scipy.special import gamma

def gamma_peak(t, A, t0, k, theta):
    """
    Gamma peak function extracted from analise_gamma.py
    """
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y
