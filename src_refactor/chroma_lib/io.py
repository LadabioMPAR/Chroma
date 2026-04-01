import pandas as pd
import os
try:
    from netCDF4 import Dataset
except ImportError:
    Dataset = None

def load_chromatogram(filepath):
    """
    Loads a chromatogram from a CSV file.
    Returns: time (np.array), signal (np.array)
    """
    df = pd.read_csv(filepath)
    # Handle cases where header might be missing or different names
    if "time" in df.columns and "signal" in df.columns:
        return df["time"].values, df["signal"].values
    elif df.shape[1] >= 2:
        # Fallback to first two columns
        return df.iloc[:, 0].values, df.iloc[:, 1].values
    else:
        raise ValueError(f"Could not parse chromatogram from {filepath}")

def load_cdf_metadata_and_signal(filepath):
    """
    Reads a CDF file and returns a dictionary with metadata and signal.
    Requires netCDF4.
    """
    if Dataset is None:
        raise ImportError("netCDF4 is required to read CDF files.")

    ds = Dataset(filepath, "r")
    
    try:
        # Metadados
        meta = {a: getattr(ds, a) for a in ds.ncattrs()}
        
        # Sinal
        intensidade = ds.variables["ordinate_values"][:]
        dt = float(ds.variables["actual_sampling_interval"][:])
        delay = float(ds.variables["actual_delay_time"][:])
        
        return {
            "metadata": meta,
            "signal": intensidade,
            "dt": dt,
            "delay": delay
        }
    finally:
        ds.close()

