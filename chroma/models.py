"""Modelos de pico — registro plugável.

Cada modelo descreve:
    - `param_names`: nomes ordenados dos parâmetros;
    - `function(t, *params)`: a curva do pico;
    - `area(*params)`: área analítica (ou None -> integra numericamente);
    - `initial_guess(...)` e `bounds(...)`: chutes/limites para o ajuste individual.

O `gamma` está implementado exatamente como nos scripts originais. Para
adicionar um modelo novo (p.ex. EMG), basta criar uma subclasse de `PeakModel`
decorada com `@register_model("nome")`.
"""

import numpy as np
from scipy.special import gamma as _gamma_fn

_REGISTRY = {}


def register_model(name):
    def deco(cls):
        _REGISTRY[name] = cls
        cls.name = name
        return cls
    return deco


def get_model(name):
    if name not in _REGISTRY:
        raise KeyError(
            f"Modelo '{name}' não registrado. Disponíveis: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]()


def available_models():
    return sorted(_REGISTRY)


class PeakModel:
    """Interface base de um modelo de pico."""

    name = None
    param_names = ()

    def function(self, t, *params):
        raise NotImplementedError

    def area(self, *params):
        """Área analítica do pico. Retorne None para integrar numericamente."""
        return None

    def initial_guess(self, peak_time, peak_height, dt, **opts):
        raise NotImplementedError

    def bounds(self, guess):
        raise NotImplementedError


# ============================================================
#  Gamma  (modelo principal — matemática idêntica à original)
# ============================================================
@register_model("gamma")
class GammaPeak(PeakModel):
    param_names = ("A", "t0", "k", "theta")

    def function(self, t, A, t0, k, theta):
        y = np.zeros_like(t)
        mask = t > t0
        x = t[mask] - t0
        y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * _gamma_fn(k))
        return y

    def area(self, A, t0, k, theta):
        # A curva é A vezes uma PDF Gamma (que integra 1), logo a área é A.
        return A

    def initial_guess(self, peak_time, peak_height, dt, randomize_k=False, **opts):
        k0 = 1.5 + np.random.rand() * 2.0 if randomize_k else 1.5
        return {
            "A": peak_height,
            "t0": peak_time - 0.05,
            "k": k0,
            "theta": dt * 5,
        }

    def bounds(self, guess):
        t0_0 = guess["t0"]
        return {
            "A": (0, np.inf),
            "t0": (t0_0 - 0.5, t0_0 + 0.5),
            "k": (0.1, 10),
            "theta": (0.001, 2),
        }


# ============================================================
#  Gaussiana  (segundo modelo, para demonstrar a pluggabilidade)
# ============================================================
@register_model("gaussian")
class GaussianPeak(PeakModel):
    param_names = ("A", "mu", "sigma")

    def function(self, t, A, mu, sigma):
        return A * np.exp(-0.5 * ((t - mu) / sigma) ** 2)

    def area(self, A, mu, sigma):
        return A * sigma * np.sqrt(2 * np.pi)

    def initial_guess(self, peak_time, peak_height, dt, **opts):
        return {"A": peak_height, "mu": peak_time, "sigma": dt * 3}

    def bounds(self, guess):
        mu0 = guess["mu"]
        return {
            "A": (0, np.inf),
            "mu": (mu0 - 0.5, mu0 + 0.5),
            "sigma": (1e-4, 2),
        }


# ------------------------------------------------------------
#  Stub para modelos futuros — descomente e implemente.
#
# @register_model("emg")
# class ExpModGaussian(PeakModel):
#     """Exponentially Modified Gaussian — bom para picos com cauda."""
#     param_names = ("A", "mu", "sigma", "tau")
#     def function(self, t, A, mu, sigma, tau):
#         ...
#     def initial_guess(self, peak_time, peak_height, dt, **opts):
#         ...
#     def bounds(self, guess):
#         ...
# ------------------------------------------------------------
