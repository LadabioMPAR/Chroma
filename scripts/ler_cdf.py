"""Ferramenta: ler CDF -> CSV.

Converte os arquivos .cdf de [paths].raw_cdf em cromatogramas CSV (colunas
time, signal), um PNG por arquivo, e um resumo com os metadados.

Uso:
    python scripts/ler_cdf.py
"""

import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tqdm import tqdm
from chroma import config, io, plotting

RESUMO_COLS = [
    "arquivo", "sample_name", "injection_date_time_stamp",
    "sample_id_comments", "sample_type", "sample_injection_volume",
    "sample_amount", "detector_name", "detector_unit", "retention_unit",
    "n_pontos", "tempo_final_min",
]


def main():
    cfg = config.load_config()
    paths = cfg["paths"]

    raw_dir = config.resolve(paths["raw_cdf"])
    chrom_dir = config.ensure_dir(paths["chromatograms"])
    plots_dir = config.ensure_dir(paths["plots"])
    resumo_path = config.resolve(paths["summary_csv"])
    os.makedirs(os.path.dirname(resumo_path), exist_ok=True)

    cdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".cdf")]
    print(f"Encontrados {len(cdf_files)} arquivos .cdf em '{raw_dir}'.")

    with open(resumo_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=RESUMO_COLS)
        writer.writeheader()

        for fname in tqdm(cdf_files, desc="Lendo CDF", unit="arquivo"):
            data = io.read_cdf(os.path.join(raw_dir, fname))
            meta = data["meta"]
            time_min = data["time_min"]
            signal = data["signal"]

            sample_name = meta.get("sample_name", os.path.splitext(fname)[0]).strip()

            out_csv = io.unique_name(os.path.join(chrom_dir, f"{sample_name}.csv"))
            io.save_chromatogram(out_csv, time_min, signal)

            out_png = io.unique_name(os.path.join(plots_dir, f"{sample_name}.png"))
            plotting.plot_raw(time_min, signal, sample_name, out_png)

            writer.writerow({
                "arquivo": fname,
                "sample_name": sample_name,
                "injection_date_time_stamp": meta.get("injection_date_time_stamp", ""),
                "sample_id_comments": meta.get("sample_id_comments", ""),
                "sample_type": meta.get("sample_type", ""),
                "sample_injection_volume": meta.get("sample_injection_volume", ""),
                "sample_amount": meta.get("sample_amount", ""),
                "detector_name": meta.get("detector_name", ""),
                "detector_unit": meta.get("detector_unit", ""),
                "retention_unit": meta.get("retention_unit", ""),
                "n_pontos": len(signal),
                "tempo_final_min": float(time_min[-1]) if len(time_min) > 0 else 0,
            })

    print(f"\nOK!\n- Resumo:        {resumo_path}\n- Cromatogramas: {chrom_dir}/\n- Plots:         {plots_dir}/")


if __name__ == "__main__":
    main()
