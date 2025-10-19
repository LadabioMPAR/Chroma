import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.special import gamma
from scipy.optimize import curve_fit

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

picos = pd.DataFrame({
    "index": peaks,
    "time": time[peaks],
    "height": signal[peaks]
})
print("Picos detectados:")
print(picos)

# ----------------------------
# 3. Função Gamma
# ----------------------------
def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y

# ----------------------------
# 4. Preparar arrays para ajustes
# ----------------------------
fit_full = np.zeros_like(signal)
areas = []
fit_peaks = []  # Armazenar ajuste de cada pico

# Cores contrastantes (tab20)
colors = plt.cm.tab20(np.linspace(0, 1, len(peaks)))

# ----------------------------
# 5. Ajuste de cada pico
# ----------------------------
for i, pico_idx in enumerate(peaks):
    pico_time = time[pico_idx]
    
    # Janela de ajuste
    extra = (time[1] - time[0]) * 10
    t_start = max(time[0], pico_time - extra)
    t_end   = min(time[-1], pico_time + extra)
    mask = (time >= t_start) & (time <= t_end)
    t_peak = time[mask]
    y_peak = signal[mask]
    
    # Estimativa inicial
    A0 = signal[pico_idx]
    t0 = pico_time
    k0 = 3
    theta0 = 0.2
    p0 = [A0, t0, k0, theta0]
    
    # Ajuste
    bounds_lower = [0, t0 - 0.5, 0.5, 0.001]
    bounds_upper = [np.inf, t0 + 0.5, 10, 5]
    params_opt, _ = curve_fit(gamma_peak, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))
    
    # Reconstrução completa
    fit_peak_full = gamma_peak(time, *params_opt)
    fit_full += fit_peak_full
    fit_peaks.append(fit_peak_full)
    
    # Área aproximada
    A, t0, k, theta = params_opt
    area = A * theta
    areas.append(area)

# ----------------------------
# 6. Plot final com áreas preenchidas
# ----------------------------
plt.figure(figsize=(12,6))
plt.plot(time, signal, color='black', lw=1.5, label="Cromatograma")

# Fill between para cada pico individual com legenda mostrando a área
for i, fit_peak_full in enumerate(fit_peaks):
    plt.fill_between(time, 0, fit_peak_full, color=colors[i], alpha=0.5, 
                     label=f"Pico {i+1}, Área ≈ {areas[i]:.2f}")

# Linha da soma de todos os ajustes (opcional)
plt.plot(time, fit_full, "r--", lw=2, label="Soma de ajustes Gamma")

plt.scatter(time[peaks], signal[peaks], color='black', s=50, label="Picos detectados")
plt.xlabel("Tempo")
plt.ylabel("Sinal")
plt.title("Cromatograma ajustado (função gamma)")
plt.legend(loc='upper right', fontsize=9)
plt.tight_layout()
plt.savefig("plots/cromatograma_ajustado_gamma_areas.png", dpi=300)
plt.show()

# ----------------------------
# 7. Resultados
# ----------------------------
for i, area in enumerate(areas):
    print(f"Pico {i+1} (t ≈ {time[peaks[i]]:.2f}): Área aproximada = {area:.3f}")
