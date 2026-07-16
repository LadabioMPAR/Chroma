"""Passo 04 — Ajuste TRAVADO.

Para cada CSV em [locked_fit].input_dir: fixa k e theta (vindos do passo 03,
ou informados manualmente no config) e ajusta apenas os demais parâmetros do
pico (A e t0, no gamma). Exporta amplitude, t0, área e R² por pico, além dos
gráficos e do CSV de reconstrução de cada cromatograma.

Uso:
    python scripts/04_ajuste_travado.py
"""

import os
import sys
import glob
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from tqdm import tqdm

from chroma import config, io, peaks, fitting, plotting

warnings.filterwarnings("ignore", category=RuntimeWarning)


def _resolve_ktheta(cfg):
    """Resolve k e theta a partir do config: números diretos ou 'auto' (passo 03)."""
    lf = cfg["locked_fit"]
    k_cfg, theta_cfg = lf["k"], lf["theta"]

    need_auto = (k_cfg == "auto") or (theta_cfg == "auto")
    if need_auto:
        ktheta_path = cfg["estimate_k_theta"]["ktheta_out"]
        try:
            k_auto, theta_auto = config.load_ktheta(ktheta_path)
        except FileNotFoundError:
            raise SystemExit(
                f"k/theta = 'auto', mas '{config.resolve(ktheta_path)}' não existe.\n"
                "Rode antes o passo 03 (scripts/03_estimar_k_theta.py) "
                "ou escreva os valores de k e theta no config.toml."
            )
    k = k_auto if k_cfg == "auto" else float(k_cfg)
    theta = theta_auto if theta_cfg == "auto" else float(theta_cfg)
    return k, theta


def main():
    cfg = config.load_config()
    paths = cfg["paths"]
    lf = cfg["locked_fit"]
    model_name = lf.get("model", "gamma")

    k_fix, theta_fix = _resolve_ktheta(cfg)
    print(f"Parâmetros travados:  k = {k_fix}   theta = {theta_fix}")

    input_dir = config.resolve(lf["input_dir"])
    nome_pasta = os.path.basename(input_dir.rstrip("/\\"))

    plots_dir = config.ensure_dir(os.path.join(paths["plots"], nome_pasta + "_travado"))
    residuos_dir = config.ensure_dir(os.path.join(plots_dir, "residuos"))
    fits_dir = config.ensure_dir(os.path.join(plots_dir, "fits"))
    results_dir = config.ensure_dir(os.path.join(paths["results"], nome_pasta + "_travado"))

    arquivos = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    print(f"Encontrados {len(arquivos)} arquivos em '{input_dir}'.")

    registros = []
    for caminho in tqdm(arquivos, desc="Ajustando (travado)", unit="arquivo"):
        nome = os.path.basename(caminho)
        nome_base = os.path.splitext(nome)[0]

        time, signal = io.load_chromatogram(caminho)
        idxs = peaks.detect(signal, lf["peaks"])
        if len(idxs) == 0:
            print(f"Nenhum pico encontrado em {nome}")
            continue

        peak_results = fitting.fit_peaks_individual(
            time, signal, idxs,
            model_name=model_name,
            extra_window=lf.get("extra_window", 10),
            fixed={"k": k_fix, "theta": theta_fix},
        )

        # CSV de reconstrução (time, signal, fit_total, peak_i)
        fit_total = np.sum([pr["curve"] for pr in peak_results], axis=0)
        fit_df = pd.DataFrame({"time": time, "signal": signal, "fit_total": fit_total})
        for i, pr in enumerate(peak_results):
            fit_df[f"peak_{i + 1}"] = pr["curve"]
        fit_df.to_csv(os.path.join(fits_dir, f"{nome_base}_fit.csv"), index=False)

        # Parâmetros e áreas por pico
        for i, pr in enumerate(peak_results):
            p = pr["params"]
            registros.append({
                "arquivo": nome,
                "pico": i + 1,
                "tempo_pico": round(pr["peak_time"], 1),
                "amplitude": p.get("A", np.nan),
                "t0": p.get("t0", np.nan),
                "k": k_fix,
                "theta": theta_fix,
                "area": pr["area"],
                "R2": pr["R2"],
            })

        plotting.plot_individual_fit(
            time, signal, peak_results, nome,
            os.path.join(plots_dir, f"{nome_base}_ajuste.png"),
            show_area=True,
        )
        plotting.plot_residuals(
            time, signal, fit_total, nome,
            os.path.join(residuos_dir, f"{nome_base}_residuos.png"),
        )

    pd.DataFrame(registros).to_csv(os.path.join(results_dir, "resultados.csv"), index=False)

    print("\nAnálise concluída!")
    print(f"Resultados: {os.path.join(results_dir, 'resultados.csv')}")
    print(f"Gráficos:   {plots_dir}")
    print(f"Fits (CSV): {fits_dir}")


if __name__ == "__main__":
    main()
