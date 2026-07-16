import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.special import gamma
from tqdm import tqdm
import glob
import os
from tkinter import Tk, filedialog
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ----------------------------
# Parâmetros ajustáveis
# ----------------------------
PROMINENCE = 0.1         # prominence para find_peaks
DISTANCE = 1               # distância mínima entre picos
EXTRA_WINDOW = 10           # janela extra para ajuste (em múltiplos do delta t)

# ----------------------------
# Selecionar pasta de entrada
# ----------------------------
Tk().withdraw()
pasta = filedialog.askdirectory(title="Selecione a pasta com os cromatogramas")
if not pasta:
    raise SystemExit("Nenhuma pasta selecionada. Encerrando.")

# Nome da pasta para salvar CSV e plots
nome_pasta = os.path.basename(pasta.rstrip("/\\"))

# ----------------------------
# Função GAMMA
# ----------------------------
def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y

# ----------------------------
# Criar pastas de saída
# ----------------------------
plots_saida = os.path.join("plots", nome_pasta)
plots_residuos = os.path.join(plots_saida, "residuos")
os.makedirs(plots_saida, exist_ok=True)
os.makedirs(plots_residuos, exist_ok=True)
os.makedirs("resultados", exist_ok=True)

# ----------------------------
# Obter todos os arquivos CSV
# ----------------------------
arquivos = sorted(glob.glob(os.path.join(pasta, "*.csv")))
print(f"Encontrados {len(arquivos)} arquivos para análise em '{pasta}'.")

# ----------------------------
# Lista para armazenar resultados
# ----------------------------
resultados = []

# ----------------------------
# Loop principal com tqdm
# ----------------------------
for caminho_csv in tqdm(arquivos, desc="Processando cromatogramas", unit="arquivo"):
    nome_arquivo = os.path.basename(caminho_csv)

    # Carregar dados
    df = pd.read_csv(caminho_csv)
    time = df["time"].values
    signal = df["signal"].values

    # Detectar picos
    peaks, _ = find_peaks(signal, prominence=PROMINENCE, distance=DISTANCE)
    if len(peaks) == 0:
        continue

    # Preparar arrays para gráficos
    fit_full = np.zeros_like(signal)
    fit_peaks = []
    areas = []
    colors = plt.cm.tab20(np.linspace(0, 1, len(peaks)))

    # Ajustar cada pico
    for i, pico_idx in enumerate(peaks):
        pico_time = time[pico_idx]

        # Janela de ajuste
        t_start = max(time[0], pico_time - EXTRA_WINDOW * (time[1] - time[0]))
        t_end = min(time[-1], pico_time + EXTRA_WINDOW * (time[1] - time[0]))
        mask = (time >= t_start) & (time <= t_end)
        t_peak = time[mask]
        y_peak = signal[mask]

        # Estimativas iniciais
        A0 = signal[pico_idx]
        t0_0 = pico_time - 0.05
        k0 = 1.5 + np.random.rand() * 2.0
        theta0 = (time[1] - time[0]) * 5
        p0 = [A0, t0_0, k0, theta0]

        # Limites
        bounds_lower = [0, t0_0 - 0.5, 0.1, 0.001]
        bounds_upper = [np.inf, t0_0 + 0.5, 10, 2]

        try:
            # Ajuste
            params_opt, _ = curve_fit(gamma_peak, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))
            fit_peak_full = gamma_peak(time, *params_opt)
            fit_full += fit_peak_full
            fit_peaks.append(fit_peak_full)

            # R² do ajuste
            fit_local = gamma_peak(t_peak, *params_opt)
            ss_res = np.sum((y_peak - fit_local) ** 2)
            ss_tot = np.sum((y_peak - np.mean(y_peak)) ** 2)
            r2 = 1 - ss_res / ss_tot

            # Área
            area = np.trapezoid(fit_peak_full, time)
            areas.append(area)

            # Registrar resultado
            resultados.append({
                "arquivo": nome_arquivo,
                "tempo_pico": round(pico_time, 1),
                "amplitude": params_opt[0],
                "k": params_opt[2],
                "theta": params_opt[3],
                "area": area,
                "R2": r2
            })

        except Exception:
            resultados.append({
                "arquivo": nome_arquivo,
                "tempo_pico": round(pico_time, 1),
                "amplitude": np.nan,
                "k": np.nan,
                "theta": np.nan,
                "area": np.nan,
                "R2": np.nan
            })
            continue

    # ----------------------------
    # Plot cromatograma principal
    # ----------------------------
    plt.figure(figsize=(12, 6))
    plt.plot(time, signal, color='black', lw=1.5, label="Cromatograma")
    for i, fit_peak_full in enumerate(fit_peaks):
        plt.fill_between(time, 0, fit_peak_full, color=colors[i], alpha=0.5,
                         label=f"Pico {round(time[peaks[i]],1)}, Área ≈ {areas[i]:.2f}")
    plt.plot(time, fit_full, 'r--', lw=2, label="Soma de ajustes Gamma")
    plt.scatter(time[peaks], signal[peaks], color='black', s=50, label="Picos detectados")
    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"Cromatograma ajustado (Gamma) — {nome_arquivo}")
    plt.legend(loc='upper right', fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(f"{plots_saida}/{os.path.splitext(nome_arquivo)[0]}_ajuste_gamma.png",
                dpi=300, bbox_inches='tight')
    plt.close()

    # ----------------------------
    # Plot de resíduos separado
    # ----------------------------
    plt.figure(figsize=(12, 4))
    residuos = signal - fit_full
    plt.axhline(0, color='black', lw=1, linestyle='--', label="Zero")
    for i, fit_peak_full in enumerate(fit_peaks):
        # Mostrar contribuição de cada pico no resíduo
        plt.plot(time, fit_peak_full, color=colors[i], alpha=0.7, lw=1,
                 label=f"Pico {round(time[peaks[i]],1)}")
    plt.plot(time, residuos, color='blue', lw=1.5, label="Resíduo total")
    plt.xlabel("Tempo")
    plt.ylabel("Resíduo")
    plt.title(f"Resíduos do ajuste Gamma — {nome_arquivo}")
    plt.legend(loc='upper right', fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(f"{plots_residuos}/{os.path.splitext(nome_arquivo)[0]}_residuos.png",
                dpi=300, bbox_inches='tight')
    plt.close()

# ----------------------------
# Salvar resultados consolidados
# ----------------------------
csv_saida = f"resultados/parametros_ajuste_gamma_{nome_pasta}.csv"
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv(csv_saida, index=False)

print("\n Análise concluída!")
print(f"Resultados salvos em: {csv_saida}")
print(f"Gráficos principais salvos em: {plots_saida}")
print(f"Gráficos de resíduos salvos em: {plots_residuos}")
