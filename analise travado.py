import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.special import gamma
import matplotlib.pyplot as plt
import glob
import os

#===============================================================
# 1) FUNÇÃO GAMMA ORIGINAL
#===============================================================
def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y

#===============================================================
# 2) VERSÃO COM k E θ FIXOS (apenas A e t0 são ajustados)
#===============================================================
def gamma_peak_fixed(t, A, t0, k_fixed, theta_fixed):
    return gamma_peak(t, A, t0, k_fixed, theta_fixed)

#===============================================================
# 3) SOMA DE VÁRIOS PICOS
#===============================================================
def multi_gamma_fixed(t, *params, k_fixed, theta_fixed):
    n = len(params) // 2   # (A, t0) para cada pico
    y_total = np.zeros_like(t)

    for i in range(n):
        A = params[2*i]
        t0 = params[2*i + 1]

        y_total += gamma_peak_fixed(
            t, A, t0, k_fixed, theta_fixed
        )

    return y_total

#===============================================================
# 4) FUNÇÃO QUE AJUSTA UM CROMATOGRAMA
#===============================================================
def ajustar_cromatograma(filepath, k_fixado, theta_fixado, altura_rel=0.05, dist_min=20):
    print(f"\nAjustando: {filepath}")

    df = pd.read_csv(filepath)
    t = df.iloc[:, 0].values
    y = df.iloc[:, 1].values

    #-----------------------------------------------------------
    # DETECÇÃO DE PICOS AUTOMÁTICA
    #-----------------------------------------------------------
    min_height = altura_rel * max(y)
    indices, props = find_peaks(y, height=min_height, distance=dist_min)

    if len(indices) == 0:
        print("Nenhum pico encontrado!")
        return None

    t0_iniciais = t[indices]
    A_iniciais = y[indices]
    n_picos = len(indices)

    #-----------------------------------------------------------
    # CHUTES INICIAIS INTERCALANDO A e t0
    #-----------------------------------------------------------
    guess = []
    for A, t0 in zip(A_iniciais, t0_iniciais):
        guess.append(A)     # amplitude inicial
        guess.append(t0)    # posição inicial

    #-----------------------------------------------------------
    # AJUSTE
    #-----------------------------------------------------------
    popt, pcov = curve_fit(
        lambda t, *params: multi_gamma_fixed(
            t, *params,
            k_fixed=k_fixado,
            theta_fixed=theta_fixado
        ),
        t, y,
        p0=guess,
        maxfev=50000
    )

    #-----------------------------------------------------------
    # PLOT
    #-----------------------------------------------------------
    plt.figure(figsize=(10,6))
    plt.plot(t, y, label="Original", linewidth=2)

    y_fit = multi_gamma_fixed(t, *popt, k_fixed=k_fixado, theta_fixed=theta_fixado)
    plt.plot(t, y_fit, '--', label="Ajuste total", linewidth=2)

    # picos individuais
    for i in range(n_picos):
        A = popt[2*i]
        t0 = popt[2*i + 1]
        yi = gamma_peak_fixed(t, A, t0, k_fixado, theta_fixado)
        plt.plot(t, yi, label=f"Pico {i+1}")

    plt.legend()
    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"Deconvolução Gamma — k={k_fixado}, θ={theta_fixado}")
    plt.tight_layout()
    plt.show()

    return popt, pcov, indices

#===============================================================
# 5) PROCESSAR UMA PASTA INTEIRA
#===============================================================
def processar_pasta(pasta, k_fixado, theta_fixado):
    arquivos = glob.glob(os.path.join(pasta, "*.csv"))
    resultados = []

    for arq in arquivos:
        r = ajustar_cromatograma(arq, k_fixado, theta_fixado)
        if r is None:
            continue

        popt, pcov, indices = r
        resultados.append([arq] + list(popt))

    # salvar CSV de resultados
    df = pd.DataFrame(resultados)
    df.to_csv("resultados_deconvolucao.csv", index=False)
    print("\n✔ Resultados salvos em 'resultados_deconvolucao.csv'")

#===============================================================
#
#===============================================================
if __name__ == "__main__":
    # defina aqui os valores fixos desejados:
    K = 3.1274011524896435
    theta = 0.11818353095360798

    pasta = "cromatogramas/EXP 5"
    processar_pasta(pasta, K, theta)
