"""Análise travada (calibrar + analisar) — usada por scripts/analisar.py.

Duas funções, que a ferramenta `analisar` encadeia, mas que também podem ser
usadas separadamente na biblioteca:

    estimate_ktheta(...)   padrões  -> k, theta   (ajuste global; exige gamma)
    analyze_samples(...)   amostras -> áreas       (ajuste travado, k/theta fixos)

A matemática vem inteira dos módulos `fitting_global` e `fitting`; aqui só se
carrega os arquivos, gera relatórios e gráficos.
"""

import os
import glob

import numpy as np
import pandas as pd

from . import config, io, peaks, fitting, fitting_global, plotting
from .models import get_model


# ============================================================
#  Etapa A — estimar k e theta a partir dos PADRÕES (ajuste global)
# ============================================================
def estimate_ktheta(
    standards_glob,
    peaks_cfg,
    model_name="gamma",
    k0=5.0,
    theta0=0.2,
    plots_dir=None,
    report_csv=None,
    ktheta_out=None,
    verbose=2,
):
    """Ajuste global dos padrões; devolve (k, theta).

    Se `plots_dir`, `report_csv` ou `ktheta_out` forem dados, grava também os
    gráficos por padrão, o relatório de picos e o JSON com k/theta.
    """
    files = sorted(glob.glob(config.resolve(standards_glob)))
    if not files:
        raise SystemExit(f"Nenhum padrão encontrado em '{config.resolve(standards_glob)}'.")

    all_t, all_y, peaks_list = [], [], []
    for f in files:
        t, y = io.load_chromatogram(f)
        all_t.append(t)
        all_y.append(y)
        peaks_list.append(peaks.detect(y, peaks_cfg))

    result, n_peaks_list, k, theta = fitting_global.fit_global_shared_ktheta(
        all_t, all_y, peaks_list, model_name=model_name, k0=k0, theta0=theta0, verbose=verbose
    )

    # Relatório + gráficos por padrão (reconstruindo A, mu de result.x)
    model = get_model(model_name)
    if plots_dir:
        config.ensure_dir(plots_dir)
    params = result.x
    idx = 2
    registros = []
    for f, t, y, n_peaks in zip(files, all_t, all_y, n_peaks_list):
        nome = os.path.splitext(os.path.basename(f))[0]
        curves = []
        for j in range(n_peaks):
            A = params[idx]
            mu = params[idx + 1]
            curves.append(model.function(t, A, mu, k, theta))
            registros.append({
                "arquivo": nome, "pico_id": j + 1, "A": A, "mu": mu,
                "k_global": k, "theta_global": theta,
            })
            idx += 2
        if plots_dir:
            plotting.plot_global_fit(t, y, curves, nome,
                                     os.path.join(config.resolve(plots_dir), f"{nome}_fit.png"))

    if report_csv:
        out = config.resolve(report_csv)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pd.DataFrame(registros).to_csv(out, index=False)
    if ktheta_out:
        config.save_ktheta(ktheta_out, k, theta,
                           extra={"n_cromatogramas": len(files), "modelo": model_name})

    return k, theta


# ============================================================
#  Etapa B — analisar AMOSTRAS com k e theta travados
# ============================================================
def analyze_samples(
    samples_glob,
    peaks_cfg,
    k,
    theta,
    model_name="gamma",
    extra_window=10,
    plots_dir=None,
    fits_dir=None,
    residuos_dir=None,
    results_csv=None,
):
    """Ajuste travado (k, theta fixos) de cada amostra; devolve DataFrame de picos.

    Grava, se os caminhos forem dados: CSV de reconstrução por amostra (fits_dir),
    gráficos de ajuste (plots_dir) e resíduos (residuos_dir), e o CSV consolidado
    (results_csv) com amplitude, t0, k, theta, área e R² por pico.
    """
    files = sorted(glob.glob(config.resolve(samples_glob)))
    for d in (plots_dir, fits_dir, residuos_dir):
        if d:
            config.ensure_dir(d)

    registros = []
    for caminho in files:
        nome = os.path.basename(caminho)
        nome_base = os.path.splitext(nome)[0]

        time, signal = io.load_chromatogram(caminho)
        idxs = peaks.detect(signal, peaks_cfg)
        if len(idxs) == 0:
            print(f"Nenhum pico encontrado em {nome}")
            continue

        peak_results = fitting.fit_peaks_individual(
            time, signal, idxs, model_name=model_name,
            extra_window=extra_window, fixed={"k": k, "theta": theta},
        )

        fit_total = np.sum([pr["curve"] for pr in peak_results], axis=0)

        if fits_dir:
            fit_df = pd.DataFrame({"time": time, "signal": signal, "fit_total": fit_total})
            for i, pr in enumerate(peak_results):
                fit_df[f"peak_{i + 1}"] = pr["curve"]
            fit_df.to_csv(os.path.join(config.resolve(fits_dir), f"{nome_base}_fit.csv"), index=False)

        for i, pr in enumerate(peak_results):
            p = pr["params"]
            registros.append({
                "arquivo": nome, "pico": i + 1, "tempo_pico": round(pr["peak_time"], 1),
                "amplitude": p.get("A", np.nan), "t0": p.get("t0", np.nan),
                "k": k, "theta": theta, "area": pr["area"], "R2": pr["R2"],
            })

        if plots_dir:
            plotting.plot_individual_fit(
                time, signal, peak_results, nome,
                os.path.join(config.resolve(plots_dir), f"{nome_base}_ajuste.png"), show_area=True)
        if residuos_dir:
            plotting.plot_residuals(
                time, signal, fit_total, nome,
                os.path.join(config.resolve(residuos_dir), f"{nome_base}_residuos.png"))

    df = pd.DataFrame(registros)
    if results_csv:
        out = config.resolve(results_csv)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        df.to_csv(out, index=False)
    return df
