"""Ferramenta: ajuste individual por pico (livre).

Ferramenta independente para estimar a área dos picos de cada cromatograma
ajustando um modelo com todos os parâmetros LIVRES. O modelo é escolhido em
[individual_fit].model — pode ser `gamma`, `gaussian` ou qualquer outro
registrado em chroma/models.py (não está preso ao gamma).

Exporta, por pico, os parâmetros do modelo escolhido + área + R².

Uso:
    python scripts/ajuste_individual.py
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


def main():
    cfg = config.load_config()
    paths = cfg["paths"]
    fit_cfg = cfg["individual_fit"]

    input_dir = config.resolve(fit_cfg["input_dir"])
    nome_pasta = os.path.basename(input_dir.rstrip("/\\"))
    model_name = fit_cfg.get("model", "gamma")

    plots_dir = config.ensure_dir(os.path.join(paths["plots"], nome_pasta))
    residuos_dir = config.ensure_dir(os.path.join(plots_dir, "residuos"))
    results_dir = config.ensure_dir(paths["results"])

    arquivos = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    print(f"Modelo: {model_name}. Encontrados {len(arquivos)} arquivos em '{input_dir}'.")

    registros = []
    for caminho in tqdm(arquivos, desc="Ajustando (livre)", unit="arquivo"):
        nome = os.path.basename(caminho)
        nome_base = os.path.splitext(nome)[0]

        time, signal = io.load_chromatogram(caminho)
        idxs = peaks.detect(signal, fit_cfg["peaks"])
        if len(idxs) == 0:
            continue

        peak_results = fitting.fit_peaks_individual(
            time, signal, idxs,
            model_name=model_name,
            extra_window=fit_cfg.get("extra_window", 10),
            fixed=None,
            guess_opts={"randomize_k": fit_cfg.get("randomize_k", True)},
        )

        # Saída genérica: uma coluna por parâmetro do modelo escolhido + área + R²
        for pr in peak_results:
            row = {"arquivo": nome, "tempo_pico": round(pr["peak_time"], 1)}
            row.update(pr["params"])
            row["area"] = pr["area"]
            row["R2"] = pr["R2"]
            registros.append(row)

        fit_total = np.sum([pr["curve"] for pr in peak_results], axis=0)
        plotting.plot_individual_fit(
            time, signal, peak_results, nome,
            os.path.join(plots_dir, f"{nome_base}_ajuste_{model_name}.png"),
            show_area=True,
        )
        plotting.plot_residuals(
            time, signal, fit_total, nome,
            os.path.join(residuos_dir, f"{nome_base}_residuos.png"),
        )

    csv_saida = os.path.join(results_dir, f"parametros_ajuste_{model_name}_{nome_pasta}.csv")
    pd.DataFrame(registros).to_csv(csv_saida, index=False)

    print("\nConcluído!")
    print(f"Resultados: {csv_saida}")
    print(f"Gráficos:   {plots_dir}")


if __name__ == "__main__":
    main()
