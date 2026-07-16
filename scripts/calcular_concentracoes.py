"""Ferramenta: calcular concentrações de uma pasta de amostras.

Varre [quantify].input_dir, ajusta os picos de cada cromatograma e calcula a
concentração de cada analito aplicando as curvas de calibração lidas de
[quantify].curves_txt (arquivo gerado por curva_calibracao.py). Para cada
analito, casa o pico ajustado mais próximo do tempo de retenção da curva e
aplica concentração = a·área + b.

Devolve uma tabela: uma linha por amostra, uma coluna por analito (concentração).

Uso:
    python scripts/calcular_concentracoes.py
"""

import os
import sys
import glob
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from tqdm import tqdm

from chroma import config, io, peaks, fitting, calibration

warnings.filterwarnings("ignore", category=RuntimeWarning)


def main():
    cfg = config.load_config()
    q = cfg["quantify"]
    model_name = q.get("model", "gamma")
    tol = q.get("peak_tolerance", 0.5)

    # Curvas (analito -> tempo_pico, a, b)
    curves = calibration.load_curves(config.resolve(q["curves_txt"]))
    filtro = q.get("analytes")
    if filtro:
        curves = [c for c in curves if c["analito"] in filtro]
    if not curves:
        raise SystemExit("Nenhuma curva carregada. Rode curva_calibracao.py ou ajuste [quantify].analytes.")

    print("Curvas carregadas:", ", ".join(f"{c['analito']}(t≈{c['tempo_pico']})" for c in curves))

    input_dir = config.resolve(q["input_dir"])
    arquivos = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    print(f"Amostras: {len(arquivos)} em '{input_dir}'\n")

    linhas = []
    for caminho in tqdm(arquivos, desc="Calculando concentrações", unit="amostra"):
        nome = os.path.basename(caminho)

        time, signal = io.load_chromatogram(caminho)
        idxs = peaks.detect(signal, q["peaks"])
        peak_results = fitting.fit_peaks_individual(
            time, signal, idxs, model_name=model_name,
            extra_window=q.get("extra_window", 10), fixed=None,
        )
        ptimes = np.array([pr["peak_time"] for pr in peak_results])
        pareas = np.array([pr["area"] for pr in peak_results])

        linha = {"arquivo": nome}
        for c in curves:
            conc = np.nan
            if len(ptimes) > 0:
                j = int(np.argmin(np.abs(ptimes - c["tempo_pico"])))
                if abs(ptimes[j] - c["tempo_pico"]) <= tol and not np.isnan(pareas[j]):
                    conc = calibration.apply_curve(pareas[j], c["a"], c["b"])
            linha[c["analito"]] = conc
        linhas.append(linha)

    output_csv = config.resolve(q["output_csv"])
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df = pd.DataFrame(linhas)
    df.to_csv(output_csv, index=False)

    print("\nConcluído!")
    print(f"Concentrações: {output_csv}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
