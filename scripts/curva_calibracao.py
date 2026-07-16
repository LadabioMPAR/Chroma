"""Ferramenta: curvas de calibração lineares por analito.

Lê um CSV de áreas já gerado (por ajuste_individual ou analisar) e, para cada
analito informado em [calibration], monta uma reta de calibração
concentração = a * área + b (b = 0 por padrão; opção de estimar b).

Para cada analito você informa o nome, o tempo do pico e os pontos da curva
(cada padrão com a concentração do analito naquele padrão). O script casa o
analito ao pico pelo tempo de retenção e o padrão à sua área, ajusta a reta e
gera o gráfico.

Uso:
    python scripts/curva_calibracao.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from chroma import config, calibration, plotting


def main():
    cfg = config.load_config()
    c = cfg["calibration"]

    areas_df = pd.read_csv(config.resolve(c["areas_csv"]))
    tol = c.get("peak_tolerance", 0.5)
    fit_intercept = c.get("fit_intercept", False)
    plots_dir = config.ensure_dir(c["plots_dir"])

    print(f"Áreas: {config.resolve(c['areas_csv'])}")
    print(f"Reta: concentração = a·área + b   (b {'estimado' if fit_intercept else '= 0'})\n")

    registros = []
    for an in c["analytes"]:
        nome = an["name"]
        peak_time = float(an["peak_time"])

        xs, ys = [], []   # x = área, y = concentração
        for p in an["points"]:
            area, err = calibration.match_area(areas_df, p["file"], peak_time, tol)
            if err:
                print(f"  [{nome}] pulando '{p['file']}': {err}")
                continue
            xs.append(area)
            ys.append(float(p["concentration"]))

        if len(xs) < 2:
            print(f"  [{nome}] pontos válidos insuficientes ({len(xs)}); analito ignorado.")
            continue

        a, b, r2, n = calibration.fit_linear(xs, ys, fit_intercept=fit_intercept)
        registros.append({
            "analito": nome, "tempo_pico": peak_time,
            "a_slope": a, "b_intercept": b, "R2": r2, "n_pontos": n,
        })

        plotting.plot_calibration(
            xs, ys, a, b, r2, nome,
            os.path.join(plots_dir, f"calibracao_{nome}.png"),
            xlabel="Área", ylabel="Concentração",
        )
        print(f"  [{nome}]  conc = {a:.5g}·área + {b:.5g}   R²={r2:.4f}  (n={n})")

    output_csv = config.resolve(c["output_csv"])
    output_txt = config.resolve(c["output_txt"])
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(output_txt), exist_ok=True)
    pd.DataFrame(registros).to_csv(output_csv, index=False)
    calibration.save_txt(output_txt, registros)

    print(f"\nConcluído! {len(registros)} curva(s).")
    print(f"Tabela (csv): {output_csv}")
    print(f"Curvas (txt): {output_txt}")
    print(f"Gráficos:     {plots_dir}")


if __name__ == "__main__":
    main()
