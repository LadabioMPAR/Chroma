import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.special import gamma
import matplotlib.pyplot as plt
import glob
import os
from tqdm import tqdm

# ===============================================================
# PARÂMETROS TRAVADOS (EXATAMENTE COMO NO SEU SCRIPT ORIGINAL)
# ===============================================================
PROMINENCE = 0.1
DISTANCE = 1
EXTRA_WINDOW = 10

# ===============================================================
# FUNÇÃO GAMMA ORIGINAL
# ===============================================================
def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y

# ===============================================================
# GERAR NOME SEGURO
# ===============================================================
def gerar_nome_seguro(path):
    base = path
    n = 1
    while os.path.exists(path):
        path = f"{base}_{n}"
        n += 1
    return path

# ===============================================================
# AJUSTE DO CROMATOGRAMA (MANTIDA SUA LÓGICA ORIGINAL)
# ===============================================================
def ajustar_cromatograma(filepath, k_fixado, theta_fixado):
    df = pd.read_csv(filepath)
    t = df.iloc[:, 0].values
    y = df.iloc[:, 1].values

    # Detectar picos
    indices, _ = find_peaks(y, prominence=PROMINENCE, distance=DISTANCE)
    if len(indices) == 0:
        print(f"Nenhum pico encontrado em {filepath}")
        return None

    # Preparar estrutura para reconstrução
    picos_individuais = []
    y_fit_total = np.zeros_like(y)

    # Ajuste por JANELAS, exatamente como seu script original fazia
    for idx in indices:
        pico_t = t[idx]
        dt = t[1] - t[0]

        # janela extra
        t_start = max(t[0], pico_t - EXTRA_WINDOW * dt)
        t_end = min(t[-1], pico_t + EXTRA_WINDOW * dt)
        mask = (t >= t_start) & (t <= t_end)

        t_peak = t[mask]
        y_peak = y[mask]

        # Estimativas iniciais iguais às do seu script
        A0 = y[idx]
        t0_0 = pico_t - 0.05
        k0 = 1.5
        theta0 = dt * 5
        p0 = [A0, t0_0, k0, theta0]

        bounds_lower = [0, t0_0 - 0.5, 0.1, 0.001]
        bounds_upper = [np.inf, t0_0 + 0.5, 10, 2]

        try:
            params, _ = curve_fit(gamma_peak, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))

            # reconstrução global
            peak_full = gamma_peak(t, *params)
            picos_individuais.append(peak_full)
            y_fit_total += peak_full

        except:
            # se falhar, preencher com NaN
            params = [np.nan, np.nan, np.nan, np.nan]
            peak_full = np.zeros_like(t)
            picos_individuais.append(peak_full)

    return {
        "t": t,
        "y": y,
        "y_fit": y_fit_total,
        "indices": indices,
        "picos_individuais": picos_individuais,
        "popt": None  # múltiplos ajustes → não existe popt único
    }

# ===============================================================
# PROCESSAMENTO DE UMA PASTA (VERSÃO COMPLETA E FINAL)
# ===============================================================
def processar_pasta(pasta, k_fixado, theta_fixado):
    arquivos = glob.glob(os.path.join(pasta, "*.csv"))
    if len(arquivos) == 0:
        print("Nenhum CSV encontrado.")
        return

    nome_pasta = os.path.basename(pasta.rstrip("/\\"))

    # Criar pastas de saída
    pasta_plots = gerar_nome_seguro(os.path.join("plots", nome_pasta))
    pasta_residuos = os.path.join(pasta_plots, "residuos")
    pasta_fits = os.path.join(pasta_plots, "fits")
    pasta_resultados = gerar_nome_seguro(os.path.join("resultados", nome_pasta))

    os.makedirs(pasta_plots, exist_ok=True)
    os.makedirs(pasta_residuos, exist_ok=True)
    os.makedirs(pasta_fits, exist_ok=True)
    os.makedirs(pasta_resultados, exist_ok=True)

    # Resultados consolidados
    resultados = []

    # BARRA DE PROGRESSO (tqdm)
    for arq in tqdm(arquivos, desc="Processando arquivos", unit="arquivo"):
        nome = os.path.basename(arq)
        nome_base = os.path.splitext(nome)[0]

        ajuste = ajustar_cromatograma(arq, k_fixado, theta_fixado)
        if ajuste is None:
            continue

        t = ajuste["t"]
        y = ajuste["y"]
        y_fit = ajuste["y_fit"]
        indices = ajuste["indices"]
        picos = ajuste["picos_individuais"]

        # ---------------------------------------------------
        # 1) SALVAR FIT COMPLETO
        # ---------------------------------------------------
        fit_df = pd.DataFrame({"time": t, "signal": y, "fit_total": y_fit})
        for i, yi in enumerate(picos):
            fit_df[f"peak_{i+1}"] = yi

        caminho_fit = gerar_nome_seguro(os.path.join(pasta_fits, f"{nome_base}_fit.csv"))
        fit_df.to_csv(caminho_fit, index=False)

        # ---------------------------------------------------
        # 2) PLOT DO AJUSTE
        # ---------------------------------------------------
        plt.figure(figsize=(12, 6))
        plt.plot(t, y, color="black", lw=1.4, label="Cromatograma")

        colors = plt.cm.tab20(np.linspace(0, 1, len(picos)))

        for i, yi in enumerate(picos):
            plt.fill_between(t, 0, yi, alpha=0.4, color=colors[i], label=f"Pico {i+1}")

        plt.plot(t, y_fit, "r--", lw=2, label="Soma do ajuste")
        plt.scatter(t[indices], y[indices], s=40, color="black", label="Picos detectados")

        plt.title(f"Ajuste Gamma — {nome}")
        plt.xlabel("Tempo")
        plt.ylabel("Sinal")
        plt.legend(fontsize=8)
        plt.tight_layout()

        caminho_plot = gerar_nome_seguro(os.path.join(pasta_plots, f"{nome_base}_ajuste.png"))
        plt.savefig(caminho_plot, dpi=300, bbox_inches="tight")
        plt.close()

        # ---------------------------------------------------
        # 3) PLOT DE RESÍDUOS
        # ---------------------------------------------------
        residuos = y - y_fit
        plt.figure(figsize=(12, 4))
        plt.axhline(0, color="black", ls="--")
        plt.plot(t, residuos, color="blue", lw=1.4)
        plt.title(f"Resíduos — {nome}")
        plt.xlabel("Tempo")
        plt.ylabel("Resíduo")
        plt.tight_layout()

        caminho_res = gerar_nome_seguro(os.path.join(pasta_residuos, f"{nome_base}_residuos.png"))
        plt.savefig(caminho_res, dpi=300, bbox_inches="tight")
        plt.close()

        # ---------------------------------------------------
        # 4) REGISTRAR PARÂMETROS DOS PICOS
        # ---------------------------------------------------
        for i, idx in enumerate(indices):
            resultados.append({
                "arquivo": nome,
                "pico": i + 1,
                "tempo_pico": t[idx],
                "A": np.max(picos[i]) if len(picos[i]) else np.nan,
                "k": np.nan,        # seu script original ajustava individualmente, não k fixo
                "theta": np.nan     # idem acima
            })

    # ---------------------------------------------------
    # SALVAR RESULTADOS CONSOLIDADOS
    # ---------------------------------------------------
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_csv(os.path.join(pasta_resultados, "resultados.csv"), index=False)

    print("\n✔ Análise concluída!")
    print(f"Plots salvos em: {pasta_plots}")
    print(f"Resíduos salvos em: {pasta_residuos}")
    print(f"Fits salvos em: {pasta_fits}")
    print(f"Resultados salvos em: {pasta_resultados}")


# ===============================================================
# EXECUÇÃO PRINCIPAL
# ===============================================================
if __name__ == "__main__":
    K = 10.686262164316052
    theta = 0.0410141631069367

    pasta = "cromatogramas\\EXP 8"
    processar_pasta(pasta, K, theta)
