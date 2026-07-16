"""Ferramenta: ler CDF -> CSV.

Converte os arquivos .cdf de [paths].raw_cdf em cromatogramas CSV (colunas
time, signal), um PNG por arquivo, e um resumo com os metadados.

Uso:
    python scripts/ler_cdf.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from chroma import config, io


def main():
    cfg = config.load_config()
    paths = cfg["paths"]

    raw_dir = config.resolve(paths["raw_cdf"])
    chrom_dir = config.ensure_dir(paths["chromatograms"])
    plots_dir = config.ensure_dir(paths["plots"])
    resumo_path = config.resolve(paths["summary_csv"])

    n_cdf = len([f for f in os.listdir(raw_dir) if f.lower().endswith(".cdf")])
    print(f"Encontrados {n_cdf} arquivos .cdf em '{raw_dir}'.")

    barra = tqdm(total=n_cdf, desc="Lendo CDF", unit="arquivo")
    criados = io.convert_cdf_folder(
        raw_dir, chrom_dir,
        plots_dir=plots_dir,
        summary_csv=resumo_path,
        on_progress=lambda i, total, nome: barra.update(1),
    )
    barra.close()

    print(f"\nOK! {len(criados)} cromatograma(s) gerado(s).")
    print(f"- Resumo:        {resumo_path}")
    print(f"- Cromatogramas: {chrom_dir}/")
    print(f"- Plots:         {plots_dir}/")


if __name__ == "__main__":
    main()
