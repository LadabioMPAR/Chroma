import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.special import erfc
from tqdm import tqdm
import glob
import os

# ----------------------------
# Função EMG
# ----------------------------
def emg(t, A, tau, sigma, lam):
    """
    Exponentially Modified Gaussian (EMG)
    A = amplitude
    tau = posição do pico
    sigma = largura gaussiana
    lam = taxa exponencial
    """
    return (A * lam / 2) * np.exp((lam / 2) * (2 * tau + lam * sigma**2 - 2 * t)) * \
           erfc((tau + lam * sigma**2 - t) / (np.sqrt(2) * sigma))

# ----------------------------
# Criar pastas de saída
# ----------------------------
os.makedirs("plots", exist_ok=True)
os.makedirs("resultados", exist_ok=True)

# ----------------------------
# Obter todos os arquivos CSV
# ----------------------------
arquivos = sorted(glob.glob("cromatogramas/*.csv"))
print(f"Encontrados {len(arquivos)} arquivos para análise.")

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
    peaks, _ = find_peaks(signal, height=2, distance=10, prominence=0.01)
    if len(peaks) == 0:
        continue

    # Preparar arrays
    fit_full = np.zeros_like(signal)
    fit_peaks = []
    areas = []
    colors = plt.cm.tab20(np.linspace(0, 1, len(peaks)))

    # Ajustar cada pico
    for i, pico_idx in enumerate(peaks):
        pico_time = time[pico_idx]

        # Janela de ajuste
        extra = (time[1] - time[0]) * 10
        t_start = max(time[0], pico_time - extra)
        t_end = min(time[-1], pico_time + extra)
        mask = (time >= t_start) & (time <= t_end)
        t_peak = time[mask]
        y_peak = signal[mask]

        # Estimativas iniciais
        A0 = signal[pico_idx]
        tau0 = pico_time
        sigma0 = 0.2
        lam0 = 1.0
        p0 = [A0, tau0, sigma0, lam0]

        # Limites
        bounds_lower = [0, tau0 - 0.5, 0.001, 0.001]
        bounds_upper = [np.inf, tau0 + 0.5, 5, 10]

        try:
            params_opt, _ = curve_fit(emg, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))
            fit_peak_full = emg(time, *params_opt)
            fit_full += fit_peak_full
            fit_peaks.append(fit_peak_full)

            # Calcular área
            area = np.trapezoid(fit_peak_full, time)
            areas.append(area)

            # Registrar resultado
            resultados.append({
                "arquivo": nome_arquivo,
                "pico": i + 1,
                "tempo_pico": params_opt[1],
                "amplitude": params_opt[0],
                "sigma": params_opt[2],
                "lambda": params_opt[3],
                "area": area
            })

        except Exception:
            continue

    # Plotar cromatograma ajustado
    plt.figure(figsize=(12, 6))
    plt.plot(time, signal, color='black', lw=1.5, label="Cromatograma")
    for i, fit_peak_full in enumerate(fit_peaks):
        plt.fill_between(time, 0, fit_peak_full, color=colors[i], alpha=0.5,
                         label=f"Pico {i+1}, Área ≈ {areas[i]:.2f}")
    plt.plot(time, fit_full, 'r--', lw=2, label="Soma de ajustes EMG")
    plt.scatter(time[peaks], signal[peaks], color='black', s=50, label="Picos detectados")
    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"Cromatograma ajustado (EMG) — {nome_arquivo}")
    plt.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(f"plots/{os.path.splitext(nome_arquivo)[0]}_ajuste_emg.png", dpi=300)
    plt.close()

# ----------------------------
# Salvar resultados consolidados
# ----------------------------
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv("resultados/areas_emg.csv", index=False)
print("\n✅ Análise concluída!")
print("Resultados salvos em: resultados/areas_emg.csv")
print("Gráficos salvos em:   plots/")
