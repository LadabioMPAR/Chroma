"""Entrada/saída: leitura de arquivos CDF do HPLC e de CSVs de cromatograma."""

import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset


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
