"""Passo 03 — Estimar k e theta dos PADRÕES (ajuste global).

Faz um único ajuste global sobre todos os cromatogramas de [estimate_k_theta].
input_glob, com k e theta compartilhados. Grava:
    - relatório por pico (A, mu, k_global, theta_global);
    - k e theta em JSON, para o passo 04 consumir;
    - um gráfico de ajuste por cromatograma.

Uso:
    python scripts/03_estimar_k_theta.py
"""

import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from chroma import config, io, peaks, fitting_global, plotting
from chroma.models import get_model


def main():
    cfg = config.load_config()
    paths = cfg["paths"]
    est = cfg["estimate_k_theta"]
    model_name = est.get("model", "gamma")
    model = get_model(model_name)

    input_glob = config.resolve(est["input_glob"])
    files = sorted(glob.glob(input_glob))
    print(f"\n>>> Ajuste global de PADRÕES — {len(files)} cromatogramas em '{input_glob}'\n")
    if not files:
        raise SystemExit("Nenhum cromatograma encontrado. Verifique [estimate_k_theta].input_glob no config.")

    all_t, all_y, peaks_list = [], [], []
    for f in files:
        t, y = io.load_chromatogram(f)
        all_t.append(t)
        all_y.append(y)
        peaks_list.append(peaks.detect(y, est["peaks"]))

    result, n_peaks_list, k_global, theta_global = fitting_global.fit_global_shared_ktheta(
        all_t, all_y, peaks_list,
        model_name=model_name,
        k0=est.get("k0", 5.0),
        theta0=est.get("theta0", 0.2),
    )

    plots_dir = config.ensure_dir(os.path.join(paths["plots"], "padroes_k_theta"))
    output_csv = config.resolve(est["output_csv"])
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    params = result.x
    idx = 2
    registros = []
    for f, t, y, n_peaks in zip(files, all_t, all_y, n_peaks_list):
        nome = os.path.splitext(os.path.basename(f))[0]
        curves = []
        for j in range(n_peaks):
            A = params[idx]
            mu = params[idx + 1]
            curves.append(model.function(t, A, mu, k_global, theta_global))
            registros.append({
                "arquivo": nome,
                "pico_id": j + 1,
                "A": A,
                "mu": mu,
                "k_global": k_global,
                "theta_global": theta_global,
            })
            idx += 2
        plotting.plot_global_fit(t, y, curves, nome,
                                 os.path.join(plots_dir, f"{nome}_fit.png"))

    pd.DataFrame(registros).to_csv(output_csv, index=False)
    ktheta_path = config.save_ktheta(
        est["ktheta_out"], k_global, theta_global,
        extra={"n_cromatogramas": len(files), "modelo": model_name},
    )

    print(f"\n>>> k     = {k_global}")
    print(f">>> theta = {theta_global}")
    print(f"\nRelatório: {output_csv}")
    print(f"k/theta:   {ktheta_path}  (usado pelo passo 04)")
    print(f"Gráficos:  {plots_dir}")


if __name__ == "__main__":
    main()
