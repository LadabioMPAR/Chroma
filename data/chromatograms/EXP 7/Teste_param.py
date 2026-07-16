import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from glob import glob

# --- Função gamma ---
def gamma_func(x, A, x0, w, k):
    return A * ((x - x0) ** (k - 1)) * np.exp(-(x - x0) / w) * (x > x0)

# --- Função soma de gammas ---
def multi_gamma(x, *params):
    n_peaks = len(params) // 4
    y = np.zeros_like(x)
    for i in range(n_peaks):
        A, x0, w, k = params[i*4:(i+1)*4]
        y += gamma_func(x, A, x0, w, k)
    return y

# --- Ajuste simples de um cromatograma ---
def fit_single_gamma(time, signal):
    # chute inicial básico
    A0 = np.max(signal)
    x0_0 = time[np.argmax(signal)]
    w0, k0 = 0.2, 2.0
    try:
        popt, _ = curve_fit(gamma_func, time, signal, p0=[A0, x0_0, w0, k0],
                            bounds=([0, min(time), 0, 0.5],
                                    [np.inf, max(time), 5, 10]))
        return popt
    except:
        return [np.nan]*4

# --- Carregar e ajustar todos os padrões ---
def ajustar_padroes(pasta):
    padroes = {"glicose": [], "celobiose": [], "xilose": []}

    for arquivo in glob(os.path.join(pasta, "*.csv")):
        nome = os.path.basename(arquivo).lower().replace(" ", "")
        df = pd.read_csv(arquivo)
        time = df.iloc[:, 0].to_numpy()
        signal = df.iloc[:, 1].to_numpy()

        if "glicose" in nome:
            padroes["glicose"].append(fit_single_gamma(time, signal))
        elif "celobise" in nome or "celobiose" in nome:
            padroes["celobiose"].append(fit_single_gamma(time, signal))
        elif "xy" in nome or "xilose" in nome:
            padroes["xilose"].append(fit_single_gamma(time, signal))

    medias = {}
    for composto, params in padroes.items():
        if len(params) == 0:
            print(f"Aviso: nenhum arquivo encontrado para {composto}.")
            medias[composto] = np.array([np.nan]*4)
        else:
            params = np.array(params)
            medias[composto] = np.nanmean(params, axis=0)
            A, x0, w, k = medias[composto]
            print(f"{composto.capitalize()} parâmetros médios: A={A:.2f}, x0={x0:.2f}, w={w:.2f}, k={k:.2f}")

    return medias


# --- Ajustar mistura com parâmetros fixos ---
def ajustar_mistura(mistura_csv, medias):
    df = pd.read_csv(mistura_csv)
    time = df.iloc[:, 0].to_numpy()
    signal = df.iloc[:, 1].to_numpy()

    # parâmetros fixos (x0, w, k)
    x0_g, w_g, k_g = medias["glicose"][1:]
    x0_c, w_c, k_c = medias["celobiose"][1:]
    x0_x, w_x, k_x = medias["xilose"][1:]

    # apenas amplitudes variam
    def modelo(time, A_g, A_c, A_x):
        y = (gamma_func(time, A_g, x0_g, w_g, k_g) +
             gamma_func(time, A_c, x0_c, w_c, k_c) +
             gamma_func(time, A_x, x0_x, w_x, k_x))
        return y

    popt, _ = curve_fit(modelo, time, signal, p0=[1, 1, 1], bounds=(0, np.inf))

    # reconstrução
    fit_g = gamma_func(time, popt[0], x0_g, w_g, k_g)
    fit_c = gamma_func(time, popt[1], x0_c, w_c, k_c)
    fit_x = gamma_func(time, popt[2], x0_x, w_x, k_x)
    total_fit = fit_g + fit_c + fit_x

    # plot
    plt.figure(figsize=(10,6))
    plt.plot(time, signal, 'k', label='Mistura (experimental)')
    plt.plot(time, total_fit, 'r--', label='Soma dos ajustes')
    plt.plot(time, fit_g, 'g', label='Glicose')
    plt.plot(time, fit_c, 'm', label='Celobiose')
    plt.plot(time, fit_x, 'purple', label='Xilose')
    plt.xlabel('Tempo (min)')
    plt.ylabel('Sinal')
    plt.legend()
    plt.tight_layout()
    plt.show()

    return popt

# --- Execução principal ---
if __name__ == "__main__":
    pasta_padroes = "cromatogramas/EXP 7/padroes_E07"
    arquivo_mistura = "cromatogramas/EXP 7/E716.csv"

    medias = ajustar_padroes(pasta_padroes)
    amps = ajustar_mistura(arquivo_mistura, medias)

    print("\nAmplitudes ajustadas na mistura:")
    print(f"Glicose: {amps[0]:.3f}")
    print(f"Celobiose: {amps[1]:.3f}")
    print(f"Xilose: {amps[2]:.3f}")
