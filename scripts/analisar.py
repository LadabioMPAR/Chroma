"""Ferramenta: analisar amostras com k e theta travados (calibra + analisa).

Ferramenta independente que:
    1) estima k e theta a partir dos PADRÕES ([analysis].standards_glob),
       via ajuste global (usa o modelo gamma);
    2) analisa as AMOSTRAS ([analysis].samples_glob) com esses k e theta
       travados, exportando as áreas.

Se [analysis].k e [analysis].theta forem números (em vez de "auto"), a
estimativa é pulada e esses valores são usados direto — útil para reaproveitar
uma calibração anterior.

Uso:
    python scripts/analisar.py
"""

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chroma import config, analysis

warnings.filterwarnings("ignore", category=RuntimeWarning)


def main():
    cfg = config.load_config()
    a = cfg["analysis"]
    model_name = a.get("model", "gamma")

    # Nome da pasta de amostras -> subpasta de saída
    samples_name = os.path.basename(os.path.dirname(config.resolve(a["samples_glob"]))) or "amostras"

    # ---- 1) k e theta: estimar dos padrões ("auto") ou usar valores fixos ----
    need_auto = (a["k"] == "auto") or (a["theta"] == "auto")
    if need_auto:
        print(">>> Estimando k e theta a partir dos PADRÕES (ajuste global)...\n")
        k_est, theta_est = analysis.estimate_ktheta(
            a["standards_glob"], a["standards_peaks"],
            model_name=model_name,
            k0=a.get("k0", 5.0), theta0=a.get("theta0", 0.2),
            plots_dir=os.path.join(cfg["paths"]["plots"], "padroes_k_theta"),
            report_csv=a.get("report_csv"),
            ktheta_out=a.get("ktheta_out"),
        )
        k = k_est if a["k"] == "auto" else float(a["k"])
        theta = theta_est if a["theta"] == "auto" else float(a["theta"])
    else:
        k, theta = float(a["k"]), float(a["theta"])
        print(">>> Usando k e theta fixos do config (estimativa pulada).")

    print(f"\n>>> k = {k}   theta = {theta}\n")

    # ---- 2) analisar as amostras com k, theta travados ----
    print(f">>> Analisando AMOSTRAS ('{samples_name}') com k e theta travados...\n")
    plots_dir = os.path.join(cfg["paths"]["plots"], samples_name + "_travado")
    results_csv = os.path.join(cfg["paths"]["results"], samples_name + "_travado", "resultados.csv")

    df = analysis.analyze_samples(
        a["samples_glob"], a["sample_peaks"], k, theta,
        model_name=model_name, extra_window=a.get("extra_window", 10),
        plots_dir=plots_dir,
        fits_dir=os.path.join(plots_dir, "fits"),
        residuos_dir=os.path.join(plots_dir, "residuos"),
        results_csv=results_csv,
    )

    n_areas = int(df["area"].notna().sum()) if len(df) else 0
    print("\nConcluído!")
    print(f"Picos ajustados (com área): {n_areas} de {len(df)}")
    print(f"Resultados: {config.resolve(results_csv)}")
    print(f"Gráficos:   {config.resolve(plots_dir)}")


if __name__ == "__main__":
    main()
