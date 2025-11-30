import os
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from tqdm import tqdm


pasta_raw = "./raw_data"  # Pasta com arquivos .cdf
dir_cromatograma = "./cromatogramas" # Pasta de saída para cromatogramas CSV
dir_plots = "./plots" # Pasta de saída para gráficos PNG
os.makedirs(dir_cromatograma, exist_ok=True)
os.makedirs(dir_plots, exist_ok=True)

# ---------------------------------------------------------
# Função para evitar sobrescrita de arquivos
# ---------------------------------------------------------
def unique_name(path):
    """
    Se o arquivo existir, incrementa sufixos _1, _2, _3...
    Retorna um caminho único.
    """
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path

    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1

    return new_path

# ---------------------------------------------------------
# Arquivo resumo
# ---------------------------------------------------------
resumo_path = "resumo.csv"
resumo_cols = [
    "arquivo", "sample_name", "injection_date_time_stamp",
    "sample_id_comments", "sample_type", "sample_injection_volume",
    "sample_amount", "detector_name", "detector_unit", "retention_unit",
    "n_pontos", "tempo_final_min"
]

with open(resumo_path, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=resumo_cols)
    writer.writeheader()

    cdf_files = [fname for fname in os.listdir(pasta_raw) if fname.lower().endswith(".cdf")]

    for fname in tqdm(cdf_files, desc="Processando arquivos CDF", unit="arquivo"):
        caminho = os.path.join(pasta_raw, fname)

        ds = Dataset(caminho, "r")

        # Metadados
        meta = {a: getattr(ds, a) for a in ds.ncattrs()}
        sample_name = meta.get("sample_name", os.path.splitext(fname)[0]).strip()

        # Sinal
        intensidade = ds.variables["ordinate_values"][:]
        dt = float(ds.variables["actual_sampling_interval"][:])
        delay = float(ds.variables["actual_delay_time"][:])
        tempo_s = np.arange(len(intensidade)) * dt + delay
        tempo_min = tempo_s / 60.0

        # Salvar CSV garantindo nome único
        out_csv = os.path.join(dir_cromatograma, f"{sample_name}.csv")
        out_csv = unique_name(out_csv)

        cromatograma = pd.DataFrame({"time": tempo_min, "signal": intensidade})
        cromatograma.to_csv(out_csv, index=False)

        # Salvar PNG garantindo nome único
        out_png = os.path.join(dir_plots, f"{sample_name}.png")
        out_png = unique_name(out_png)

        plt.figure(figsize=(10, 5))
        plt.plot(tempo_min, intensidade, color="blue")
        plt.title(f"Cromatograma - {sample_name}")
        plt.xlabel("Tempo (min)")
        plt.ylabel("Intensidade (mV)")
        plt.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.close()

        # Linha de resumo
        linha = {
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
            "n_pontos": len(intensidade),
            "tempo_final_min": float(tempo_min[-1]) if len(tempo_min) > 0 else 0
        }

        writer.writerow(linha)
        ds.close()

print(f"\nDeu bom! ^^ \n- Resumo salvo em {resumo_path}\n- Cromatogramas em {dir_cromatograma}/\n- Plots em {dir_plots}/")
