import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.special import erf, wofz, erfc, gamma as gamma_func
from scipy.optimize import curve_fit
from scipy.integrate import trapezoid
import os

# ----------------------------
# 1. Criar pasta de plots se não existir
# ----------------------------
if not os.path.exists("plots"):
    os.makedirs("plots")

# ----------------------------
# 2. Carregar dados
# ----------------------------
df = pd.read_csv("cromatogramas/DCS_GLC_12gL_20uL.csv")
time = df["time"].values
signal = df["signal"].values

# ----------------------------
# 3. Detectar picos
# ----------------------------
peaks, properties = find_peaks(signal, height=2, distance=10, prominence=0.01)

# ----------------------------
# 4. Funções de pico
# ----------------------------
def gaussian(t, A, tau, sigma):
    return A * np.exp(-((t - tau)**2)/(2*sigma**2))

def skew_normal(t, A, tau, sigma, alpha):
    return A / (np.sqrt(2*np.pi)*sigma) * np.exp(-((t - tau)**2)/(2*sigma**2)) * (1 + erf(alpha*(t - tau)/(np.sqrt(2)*sigma)))

def voigt(t, A, tau, sigma, gamma):
    z = ((t - tau) + 1j*gamma) / (sigma * np.sqrt(2))
    return A * np.real(wofz(z)) / (sigma * np.sqrt(2*np.pi))

def emg(t, A, tau, sigma, lmbd):
    return (lmbd/2) * np.exp(lmbd/2 * (2*tau + lmbd*sigma**2 - 2*t)) * erfc((tau + lmbd*sigma**2 - t)/(np.sqrt(2)*sigma)) * A

def lognormal(t, A, mu, sigma):
    t = np.maximum(t, 1e-6)
    return A / (t * sigma * np.sqrt(2*np.pi)) * np.exp(-(np.log(t) - mu)**2 / (2*sigma**2))

def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma_func(k))
    return y

models = {
    "Gaussiana": (gaussian, 3),
    "Skew-Normal": (skew_normal, 4),
    "Voigt": (voigt, 4),
    "EMG": (emg, 4),
    "Log-normal": (lognormal, 3),
    "Gamma": (gamma_peak, 4)
}

# ----------------------------
# 5. Ajuste múltiplo e métricas
# ----------------------------
results = {}

for model_name, (func, n_params) in models.items():
    fit_full = np.zeros_like(signal)
    fit_peaks = []
    areas = []
    r2_list = []
    rmse_list = []

    for i, pico_idx in enumerate(peaks):
        pico_time = time[pico_idx]
        extra = (time[1] - time[0]) * 10
        mask = (time >= pico_time - extra) & (time <= pico_time + extra)
        t_peak = time[mask]
        y_peak = signal[mask]

        # Estimativas iniciais
        A0 = signal[pico_idx]
        tau0 = pico_time
        sigma0 = 0.2
        alpha0 = 0.0
        gamma0 = 0.2
        lmbd0 = 1.0
        mu0 = np.log(max(t_peak[0], 1e-6))
        k0, theta0 = 3.0, 0.2

        # Parâmetros e limites
        if model_name == "Gaussiana":
            p0 = [A0, tau0, sigma0]; bounds=([0,tau0-0.5,0.001],[np.inf,tau0+0.5,5])
        elif model_name == "Skew-Normal":
            p0 = [A0,tau0,sigma0,alpha0]; bounds=([0,tau0-0.5,0.001,-10],[np.inf,tau0+0.5,5,10])
        elif model_name == "Voigt":
            p0 = [A0,tau0,sigma0,gamma0]; bounds=([0,tau0-0.5,0.001,0.001],[np.inf,tau0+0.5,5,5])
        elif model_name == "EMG":
            p0 = [A0,tau0,sigma0,lmbd0]; bounds=([0,tau0-0.5,0.001,0.001],[np.inf,tau0+0.5,5,10])
        elif model_name == "Log-normal":
            p0 = [A0, mu0, sigma0]; bounds=([0, mu0-1,0.001],[np.inf, mu0+1,5])
        elif model_name == "Gamma":
            p0 = [A0, tau0, k0, theta0]; bounds=([0, tau0-0.5,0.5,0.001],[np.inf, tau0+0.5,10,5])

        try:
            params_opt, _ = curve_fit(func, t_peak, y_peak, p0=p0, bounds=bounds, maxfev=5000)
        except:
            params_opt = p0

        fit_peak_full = func(time, *params_opt)
        fit_full += fit_peak_full
        fit_peaks.append(fit_peak_full)

        # Área aproximada
        if model_name == "Gamma":
            A, t0, k, theta = params_opt
            area = A * theta * gamma_func(k)
        else:
            area = trapezoid(fit_peak_full, time)
        areas.append(area)

        # Métricas
        residuals = y_peak - func(t_peak, *params_opt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_peak - np.mean(y_peak))**2)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt(np.mean(residuals**2))
        r2_list.append(r2)
        rmse_list.append(rmse)

    results[model_name] = {
        "fit_full": fit_full,
        "fit_peaks": fit_peaks,
        "areas": areas,
        "r2_list": r2_list,
        "rmse_list": rmse_list
    }

# ----------------------------
# 6. Salvar plots individuais por modelo
# ----------------------------
colors = plt.cm.tab20(np.linspace(0,1,len(peaks)))
for model_name, data in results.items():
    plt.figure(figsize=(12,6))
    plt.plot(time, signal, color='black', lw=1.5, label='Original')
    for j, fit_peak_full in enumerate(data['fit_peaks']):
        plt.fill_between(time, 0, fit_peak_full, color=colors[j], alpha=0.4)
    plt.plot(time, data['fit_full'], 'r--', lw=2, label='Soma do ajuste')
    residuals = signal - data['fit_full']
    plt.plot(time, residuals, 'k--', alpha=0.5, label='Resíduos')

    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"{model_name} - Ajuste detalhado")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(f"plots/{model_name.replace(' ','_')}_ajuste.png", dpi=300)
    plt.close()

# ----------------------------
# 7. Plot principal comparativo
# ----------------------------
fig, axes = plt.subplots(len(models), 1, figsize=(12, 3*len(models)), sharex=True)
for i, (model_name, data) in enumerate(results.items()):
    ax = axes[i]
    ax.plot(time, signal, color='black', lw=1.5, label='Original')
    for j, fit_peak_full in enumerate(data['fit_peaks']):
        ax.fill_between(time, 0, fit_peak_full, color=colors[j], alpha=0.4)
    ax.plot(time, data['fit_full'], 'r--', lw=2, label='Soma do ajuste')
    residuals = signal - data['fit_full']
    ax.plot(time, residuals, 'k--', alpha=0.5, label='Resíduos')
    ax.set_ylabel("Sinal")
    ax.set_title(f"{model_name} (R² médio ≈ {np.mean(data['r2_list']):.3f}, RMSE médio ≈ {np.mean(data['rmse_list']):.3f})")
    if i == 0:
        ax.legend(fontsize=8)

axes[-1].set_xlabel("Tempo")
plt.tight_layout()
plt.savefig("plots/comparativo_ajustes_limpo.png", dpi=300)
plt.show()

# ----------------------------
# 8. Tabelas R² e RMSE
# ----------------------------
r2_summary = {model_name: np.mean(data['r2_list']) for model_name, data in results.items()}
r2_sorted = dict(sorted(r2_summary.items(), key=lambda x: x[1], reverse=True))

rmse_summary = {model_name: np.mean(data['rmse_list']) for model_name, data in results.items()}
rmse_sorted = dict(sorted(rmse_summary.items(), key=lambda x: x[1]))

# ----------------------------
# 9. Salvar tabelas em txt (UTF-8)
# ----------------------------
with open("plots/metricas_modelos.txt", "w", encoding="utf-8") as f:
    f.write("=== R² médio por modelo (ordenado do melhor) ===\n")
    for model_name, r2 in r2_sorted.items():
        f.write(f"{model_name}: R² médio ≈ {r2:.4f}\n")
    f.write("\n=== RMSE médio por modelo (ordenado do melhor) ===\n")
    for model_name, rmse in rmse_sorted.items():
        f.write(f"{model_name}: RMSE médio ≈ {rmse:.4f}\n")

print("\n=== R² médio por modelo (ordenado do melhor) ===")
for model_name, r2 in r2_sorted.items():
    print(f"{model_name}: R² médio ≈ {r2:.4f}")

print("\n=== RMSE médio por modelo (ordenado do melhor) ===")
for model_name, rmse in rmse_sorted.items():
    print(f"{model_name}: RMSE médio ≈ {rmse:.4f}")
