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

# Configuração do arquivo resumo
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

    # Lista todos os arquivos para a barrinha de progresso
    cdf_files = [fname for fname in os.listdir(pasta_raw) if fname.lower().endswith(".cdf")]
    
    # Percorre todos os .cdf da pasta_raw com barra de progresso
    for fname in tqdm(cdf_files, desc="Processando arquivos CDF", unit="arquivo"):
        caminho = os.path.join(pasta_raw, fname)

        # Abre o arquivo
        ds = Dataset(caminho, "r")

        # Metadados globais
        meta = {a: getattr(ds, a) for a in ds.ncattrs()}
        sample_name = meta.get("sample_name", os.path.splitext(fname)[0]).strip()

        # Extrai sinal
        intensidade = ds.variables["ordinate_values"][:]
        dt = float(ds.variables["actual_sampling_interval"][:])
        delay = float(ds.variables["actual_delay_time"][:])
        tempo_s = np.arange(len(intensidade)) * dt + delay
        tempo_min = tempo_s / 60.0

        # Salva cromatograma individual em CSV 
        cromatograma = pd.DataFrame({
            "time": tempo_min,
            "signal": intensidade
        })
        out_csv = os.path.join(dir_cromatograma, f"{sample_name}.csv")
        cromatograma.to_csv(out_csv, index=False)

        # Gerando gráfico (usando sample_name)
        plt.figure(figsize=(10, 5))
        plt.plot(tempo_min, intensidade, color="blue")
        plt.title(f"Cromatograma - {sample_name}")
        plt.xlabel("Tempo (min)")
        plt.ylabel("Intensidade (mV)")
        out_png = os.path.join(dir_plots, f"{sample_name}.png")
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
