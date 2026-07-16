"""Gráficos: cromatograma bruto, ajuste (individual e global) e resíduos.

São diagnósticos — a matemática vive nos módulos de fitting. Aqui só desenha.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")   # backend sem janela; escreve direto em arquivo
import matplotlib.pyplot as plt


def plot_raw(time, signal, title, out_png):
    """Cromatograma bruto (passo 01)."""
    plt.figure(figsize=(10, 5))
    plt.plot(time, signal, color="blue")
    plt.title(f"Cromatograma - {title}")
    plt.xlabel("Tempo (min)")
    plt.ylabel("Intensidade (mV)")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()


def plot_individual_fit(time, signal, peak_results, title, out_png, show_area=True):
    """Ajuste por picos (passos 02 e 04): sinal + preenchimento por pico + soma."""
    n = len(peak_results)
    colors = plt.cm.tab20(np.linspace(0, 1, max(n, 1)))
    fit_total = np.zeros_like(signal)

    plt.figure(figsize=(12, 6))
    plt.plot(time, signal, color="black", lw=1.5, label="Cromatograma")

    for i, pr in enumerate(peak_results):
        curve = pr["curve"]
        fit_total = fit_total + curve
        if show_area:
            label = f"Pico {round(pr['peak_time'], 1)}, Área ≈ {pr['area']:.2f}"
        else:
            label = f"Pico {i + 1}"
        plt.fill_between(time, 0, curve, color=colors[i], alpha=0.5, label=label)

    plt.plot(time, fit_total, "r--", lw=2, label="Soma dos ajustes")

    idxs = [pr["peak_index"] for pr in peak_results]
    if idxs:
        plt.scatter(time[idxs], signal[idxs], color="black", s=50, label="Picos detectados")

    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"Cromatograma ajustado — {title}")
    plt.legend(loc="upper right", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def plot_residuals(time, signal, fit_total, title, out_png):
    """Resíduo total (sinal - soma dos ajustes)."""
    residuos = signal - fit_total
    plt.figure(figsize=(12, 4))
    plt.axhline(0, color="black", lw=1, linestyle="--")
    plt.plot(time, residuos, color="blue", lw=1.5, label="Resíduo total")
    plt.xlabel("Tempo")
    plt.ylabel("Resíduo")
    plt.title(f"Resíduos — {title}")
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def plot_baseline(time, signal, baseline, corrected, title, out_png):
    """Correção de linha de base: original + baseline (painel de cima) e
    sinal corrigido (painel de baixo)."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(time, signal, label="Sinal original", alpha=0.8)
    axes[0].plot(time, baseline, "r--", lw=2, label="Linha de base")
    axes[0].set_ylabel("Sinal")
    axes[0].legend()
    axes[0].set_title(f"Correção de linha de base — {title}")

    axes[1].plot(time, corrected, color="green", label="Sinal corrigido")
    axes[1].axhline(0, color="black", linestyle="--", lw=1)
    axes[1].set_xlabel("Tempo")
    axes[1].set_ylabel("Corrigido")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()


def plot_calibration(x, y, a, b, r2, title, out_png, xlabel="Área", ylabel="Concentração"):
    """Curva de calibração: pontos dos padrões + reta ajustada (y = a·x + b)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xmax = x.max() if len(x) else 1.0
    xline = np.linspace(0, xmax * 1.05, 100)

    plt.figure(figsize=(7, 6))
    plt.scatter(x, y, color="black", zorder=3, label="Padrões")
    plt.plot(xline, a * xline + b, "r-",
             label=f"y = {a:.4g}·x + {b:.4g}\nR² = {r2:.4f}")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Curva de calibração — {title}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()


def plot_global_fit(time, signal, peak_curves, title, out_png):
    """Ajuste global (passo 03): sinal + cada pico (linha) + soma."""
    y_sum = np.zeros_like(time)
    plt.figure(figsize=(10, 6))
    plt.plot(time, signal, "k-", label="Experimental")
    for j, curve in enumerate(peak_curves):
        y_sum = y_sum + curve
        plt.plot(time, curve, "--", label=f"Pico {j + 1}")
    plt.plot(time, y_sum, "r-", linewidth=2, label="Soma dos picos")
    plt.title(f"Ajuste Gamma (global) — {title}")
    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
