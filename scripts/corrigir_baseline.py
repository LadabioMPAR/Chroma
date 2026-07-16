"""Ferramenta: corrigir linha de base de espectros específicos.

Aplica correção de baseline (linear ou BEADS) aos cromatogramas indicados em
[baseline] — por um glob OU por uma lista explícita de arquivos — e salva, para
cada um, um CSV com o sinal já corrigido (na coluna `signal`, pronto para as
outras ferramentas) mais o sinal original e a baseline, além de um gráfico.

Uso:
    python scripts/corrigir_baseline.py
"""

import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tqdm import tqdm

from chroma import config, io, baseline, plotting


def _resolver_arquivos(b):
    """Lista de arquivos a corrigir: `files` (lista explícita) tem prioridade
    sobre `input_glob`."""
    if b.get("files"):
        return [config.resolve(f) for f in b["files"]]
    return sorted(glob.glob(config.resolve(b["input_glob"])))


def main():
    cfg = config.load_config()
    b = cfg["baseline"]

    method = b.get("method", "linear")
    params = dict(b.get("beads", {})) if method == "beads" else {}

    arquivos = _resolver_arquivos(b)
    out_dir = config.ensure_dir(b["output_dir"])
    plots_dir = config.ensure_dir(b["plots_dir"])

    print(f"Método: {method}. Corrigindo {len(arquivos)} espectro(s).")
    print(f"Saída (CSV): {out_dir}\nSaída (PNG): {plots_dir}\n")

    n_ok = 0
    for caminho in tqdm(arquivos, desc="Corrigindo baseline", unit="arquivo"):
        if not os.path.exists(caminho):
            print(f"[AVISO] não encontrado: {caminho}")
            continue

        base_name = os.path.splitext(os.path.basename(caminho))[0]
        time, signal = io.load_chromatogram(caminho)

        bl, corr = baseline.correct(time, signal, method=method, **params)

        # `signal` = corrigido (drop-in para as demais ferramentas); original e
        # baseline ficam guardados como colunas extras.
        pd.DataFrame({
            "time": time, "signal": corr,
            "signal_original": signal, "baseline": bl,
        }).to_csv(os.path.join(out_dir, f"{base_name}_corrigido.csv"), index=False)

        plotting.plot_baseline(
            time, signal, bl, corr, base_name,
            os.path.join(plots_dir, f"{base_name}_baseline.png"),
        )
        n_ok += 1

    print(f"\nConcluído! {n_ok} espectro(s) corrigido(s).")


if __name__ == "__main__":
    main()
