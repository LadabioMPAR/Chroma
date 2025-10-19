import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.special import erfc

# ----------------------------
# 1. Carregar dados
# ----------------------------
df = pd.read_csv("cromatogramas/DCS_E616.csv")
time = df["time"].values
signal = df["signal"].values

# ----------------------------
# 2. Detectar picos
# ----------------------------
peaks, properties = find_peaks(signal, height=0, distance=10, prominence=0.1)
picos = pd.DataFrame({"index": peaks, "time": time[peaks], "height": signal[peaks]})
print("Picos detectados:")
print(picos)

# ----------------------------
# 3. Função Exponentially Modified Gaussian (EMG)
# ----------------------------
def emg(t, A, tau, sigma, lam):
    """
    Exponentially Modified Gaussian:
    A = amplitude
    tau = posição do pico
    sigma = largura gaussiana
    lam = taxa exponencial (1/lambda)
    """
    return (A*lam/2) * np.exp((lam/2)*(2*tau + lam*sigma**2 - 2*t)) * erfc((tau + lam*sigma**2 - t)/(np.sqrt(2)*sigma))

# ----------------------------
# 4. Preparar arrays
# ----------------------------
fit_full = np.zeros_like(signal)
fit_peaks = []
areas = []
colors = plt.cm.tab20(np.linspace(0,1,len(peaks)))

# ----------------------------
# 5. Ajuste de cada pico
# ----------------------------
for i, pico_idx in enumerate(peaks):
    pico_time = time[pico_idx]

    # Janela de ajuste
    extra = (time[1] - time[0]) * 5
    t_start = max(time[0], pico_time - extra)
    t_end = min(time[-1], pico_time + extra)
    mask = (time >= t_start) & (time <= t_end)
    t_peak = time[mask]
    y_peak = signal[mask]

    # Estimativa inicial
    A0 = signal[pico_idx]
    tau0 = pico_time
    sigma0 = 0.2
    lam0 = 1.0  # taxa exponencial inicial
    p0 = [A0, tau0, sigma0, lam0]

    # Limites
    bounds_lower = [0, tau0 - 0.5, 0.001, 0.001]
    bounds_upper = [np.inf, tau0 + 0.5, 5, 10]

    # Ajuste
    params_opt, _ = curve_fit(emg, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))

    # Reconstrução completa
    fit_peak_full = emg(time, *params_opt)
    fit_full += fit_peak_full
    fit_peaks.append(fit_peak_full)

    # Área aproximada usando integração numérica
    area = np.trapz(fit_peak_full, time)
    areas.append(area)

# ----------------------------
# 6. Plot final com áreas preenchidas
# ----------------------------
plt.figure(figsize=(12,6))
plt.plot(time, signal, color='black', lw=1.5, label="Cromatograma")
for i, fit_peak_full in enumerate(fit_peaks):
    plt.fill_between(time, 0, fit_peak_full, color=colors[i], alpha=0.5, label=f"Pico {i+1}, Área ≈ {areas[i]:.2f}")

plt.plot(time, fit_full, 'r--', lw=2, label="Soma de ajustes EMG")
plt.scatter(time[peaks], signal[peaks], color='black', s=50, label="Picos detectados")
plt.xlabel("Tempo")
plt.ylabel("Sinal")
plt.title("Cromatograma ajustado (EMG)")
plt.legend(loc='upper right', fontsize=9)
plt.tight_layout()
plt.savefig("plots/cromatograma_ajustado_emg_areas.png", dpi=300)
plt.show()

# ----------------------------
# 7. Resultados
# ----------------------------
for i, area in enumerate(areas):
    print(f"Pico {i+1} (t ≈ {time[peaks[i]]:.2f}): Área ≈ {area:.3f}")
