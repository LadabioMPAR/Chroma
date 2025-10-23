import pandas as pd
import matplotlib.pyplot as plt
import scipy.signal
import seaborn as sns
from hplc.quant import Chromatogram
from hplc.io import load_chromatogram
import os
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})

# --- Carregando o cromatograma ---
input_path = 'cromatogramas/Padrões/CLB05gl 5ul.csv'
df = load_chromatogram(input_path, cols=['time', 'signal'])

# --- Extraindo nome do arquivo ---
base_name = os.path.splitext(os.path.basename(input_path))[0]

# --- Dados ---
time = df["time"].values
signal_original = df["signal"].values

# --- Ajuste linear da linha de base ---
coef = np.polyfit(time, signal_original, 1)
baseline = np.polyval(coef, time)
signal_corrigido = signal_original - baseline

# --- Substituindo coluna ---
df["signal"] = signal_corrigido

# --- Criando pasta de saída ---
output_dir = "padrões corrigidos"
os.makedirs(output_dir, exist_ok=True)

# --- Caminhos de saída ---
csv_path = os.path.join(output_dir, f"{base_name}_corrigido.csv")
fig_path = os.path.join(output_dir, f"{base_name}_corrigido.png")

# --- Salvando CSV ---
df.to_csv(csv_path, index=False)


# --- Gráfico ---
fig, axes = plt.subplots(2, 1, figsize=(10,8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

#ajuste
axes[0].plot(time, signal_original, label="Sinal original", alpha=0.8)
axes[0].plot(time, baseline, 'r--', label="Linha de base (ajuste linear)", linewidth=2)
axes[0].set_ylabel("Sinal")
axes[0].legend()
axes[0].set_title(f"Ajuste linear da linha de base - {base_name}")

# sinal corrigido
axes[1].plot(time, signal_corrigido, label="Sinal corrigido", color='green')
axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
axes[1].set_xlabel("Tempo")
axes[1].set_ylabel("Sinal corrigido")
axes[1].legend()

plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()

print(f"Tudo certo em {csv_path}")

