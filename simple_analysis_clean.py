import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from hplc.quant import Chromatogram
from hplc.io import load_chromatogram
import os
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import glob
from tqdm import tqdm

sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})


# --- Função principal para correção ---
def corrigir_cromatograma(input_path, output_dir="padrões corrigidos"):
    # Carrega o cromatograma
    df = load_chromatogram(input_path, cols=['time', 'signal'])
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Dados
    time = df["time"].values
    signal_original = df["signal"].values

    # Ajuste linear da linha de base
    coef = np.polyfit(time, signal_original, 1)
    baseline = np.polyval(coef, time)
    signal_corrigido = signal_original - baseline

    # Substitui a coluna original
    df["signal"] = signal_corrigido

    # Cria pasta de saída (se não existir)
    os.makedirs(output_dir, exist_ok=True)

    # Caminhos de saída
    csv_path = os.path.join(output_dir, f"{base_name}_corrigido.csv")
    fig_path = os.path.join(output_dir, f"{base_name}_corrigido.png")

    # Salva o CSV corrigido
    df.to_csv(csv_path, index=False)

    # Gráfico com 2 painéis
    fig, axes = plt.subplots(2, 1, figsize=(10,8), sharex=True,
                             gridspec_kw={'height_ratios': [2, 1]})
    
    # Painel superior: ajuste
    axes[0].plot(time, signal_original, label="Sinal original", alpha=0.8)
    axes[0].plot(time, baseline, 'r--', label="Linha de base (ajuste linear)", linewidth=2)
    axes[0].set_ylabel("Sinal")
    axes[0].legend()
    axes[0].set_title(f"Ajuste linear da linha de base - {base_name}")

    # Painel inferior: sinal corrigido
    axes[1].plot(time, signal_corrigido, label="Sinal corrigido", color='green')
    axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[1].set_xlabel("Tempo")
    axes[1].set_ylabel("Sinal corrigido")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    plt.close()

# --- Caminho da pasta de entrada ---
input_folder = "cromatogramas/Padrões"

# --- Lista todos os arquivos CSV ---
arquivos = glob.glob(os.path.join(input_folder, "*.csv"))

# --- Processa todos com barra de progresso ---
print(f" Corrigindo {len(arquivos)} arquivos em '{input_folder}'...\n")
for arquivo in tqdm(arquivos, desc="Processando cromatogramas", ncols=80):
    try:
        corrigir_cromatograma(arquivo)
    except Exception as e:
        print(f"\n Erro ao processar {arquivo}: {e}")

print("\nCorreção concluída! Resultados salvos em 'padrões corrigidos/'")
