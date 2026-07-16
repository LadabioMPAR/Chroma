"""Entrada/saída: leitura de arquivos CDF do HPLC e de CSVs de cromatograma."""

import os
import csv as _csv
import numpy as np
import pandas as pd
from netCDF4 import Dataset

# Colunas do resumo gerado ao converter uma pasta de CDFs.
RESUMO_COLS = [
    "arquivo", "sample_name", "injection_date_time_stamp",
    "sample_id_comments", "sample_type", "sample_injection_volume",
    "sample_amount", "detector_name", "detector_unit", "retention_unit",
    "n_pontos", "tempo_final_min",
]


def unique_name(path):
    """Se `path` já existir, acrescenta sufixos _1, _2, ... até ficar único."""
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path


def read_cdf(filepath):
    """Lê um arquivo .cdf do HPLC.

    Devolve um dict com:
        meta      -> dict com todos os atributos globais do CDF
        time_min  -> vetor de tempo em minutos (arange(n)*dt + delay, /60)
        signal    -> vetor de intensidade (ordinate_values)
    """
    ds = Dataset(filepath, "r")
    try:
        meta = {a: getattr(ds, a) for a in ds.ncattrs()}
        signal = ds.variables["ordinate_values"][:]
        dt = float(ds.variables["actual_sampling_interval"][:])
        delay = float(ds.variables["actual_delay_time"][:])
        time_s = np.arange(len(signal)) * dt + delay
        time_min = time_s / 60.0
        return {"meta": meta, "time_min": time_min, "signal": signal}
    finally:
        ds.close()


def load_chromatogram(filepath):
    """Lê um CSV de cromatograma e devolve (time, signal) como np.arrays.

    Aceita cabeçalho ("time"/"signal") ou usa as duas primeiras colunas.
    """
    df = pd.read_csv(filepath)
    if "time" in df.columns and "signal" in df.columns:
        return df["time"].values, df["signal"].values
    return df.iloc[:, 0].values, df.iloc[:, 1].values


def save_chromatogram(path, time, signal):
    """Grava um CSV de cromatograma com colunas time, signal."""
    pd.DataFrame({"time": time, "signal": signal}).to_csv(path, index=False)


def convert_cdf_folder(raw_dir, out_dir, plots_dir=None, summary_csv=None, on_progress=None):
    """Converte todos os .cdf de `raw_dir` em CSVs (time, signal) em `out_dir`.

    Opcionalmente gera um PNG por cromatograma (`plots_dir`) e um CSV de resumo
    com os metadados da injeção (`summary_csv`). `on_progress(i, total, nome)` é
    chamado a cada arquivo, para barra de progresso / log.

    Nomes que colidem recebem sufixo _1, _2, ... (nunca sobrescreve).
    Devolve a lista de CSVs criados.
    """
    os.makedirs(out_dir, exist_ok=True)
    if plots_dir:
        os.makedirs(plots_dir, exist_ok=True)

    cdf_files = sorted(f for f in os.listdir(raw_dir) if f.lower().endswith(".cdf"))
    criados, linhas = [], []

    for i, fname in enumerate(cdf_files, 1):
        data = read_cdf(os.path.join(raw_dir, fname))
        meta, time_min, signal = data["meta"], data["time_min"], data["signal"]
        sample_name = meta.get("sample_name", os.path.splitext(fname)[0]).strip()

        out_csv = unique_name(os.path.join(out_dir, f"{sample_name}.csv"))
        save_chromatogram(out_csv, time_min, signal)
        criados.append(out_csv)

        if plots_dir:
            from . import plotting   # import local: evita puxar matplotlib sem necessidade
            out_png = unique_name(os.path.join(plots_dir, f"{sample_name}.png"))
            plotting.plot_raw(time_min, signal, sample_name, out_png)

        linhas.append({
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

        if on_progress:
            on_progress(i, len(cdf_files), sample_name)

    if summary_csv:
        os.makedirs(os.path.dirname(summary_csv), exist_ok=True)
        with open(summary_csv, "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=RESUMO_COLS)
            w.writeheader()
            w.writerows(linhas)

    return criados
