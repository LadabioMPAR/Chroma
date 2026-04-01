import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import least_squares
from scipy.special import gamma
from glob import glob
import os

# ============================================================
# 1. Modelo do pico Gamma
# ============================================================
def gamma_peak(t, A, t0, k, theta):
    y = np.zeros_like(t)
    mask = t > t0
    x = t[mask] - t0
    y[mask] = A * (x ** (k - 1)) * np.exp(-x / theta) / (theta ** k * gamma(k))
    return y

# ============================================================
# 2. Função de resíduos global (picos variáveis por crom.)
# ============================================================
def residuals(params, all_t, all_y, n_picos_list):
    k, theta = params[0], params[1]
    idx = 2
    res = []

    for t, y_exp, n_picos in zip(all_t, all_y, n_picos_list):
        y_pred = np.zeros_like(t)
        for _ in range(n_picos):
            A = params[idx]
            mu = params[idx + 1]
            y_pred += gamma_peak(t, A, mu, k, theta)
            idx += 2

        res.append(y_pred - y_exp)

    return np.concatenate(res)

# ============================================================
# 3. Carregar os arquivos de cromatogramas
# ============================================================
def load_chromatograms(path):
    files = glob(path)
    all_t, all_y = [], []

    for f in files:
        df = pd.read_csv(f)
        t = df.iloc[:, 0].to_numpy()
        y = df.iloc[:, 1].to_numpy()
        all_t.append(t)
        all_y.append(y)

    return files, all_t, all_y

# ============================================================
# 4. Ajuste global com detecção automática de picos
# ============================================================
def fit_gamma_variable_peaks(path_glob, prominence=0.1, distance=5):
    files, all_t, all_y = load_chromatograms(path_glob)

    k0 = 5
    theta0 = 0.2
    params0 = [k0, theta0]

    n_picos_list = []

    # Detectar picos
    for t, y in zip(all_t, all_y):
        thr = np.max(y) * prominence
        peaks, _ = find_peaks(y, height=thr, distance=distance)

        if len(peaks) == 0:
            peaks = [np.argmax(y)]

        n_picos_list.append(len(peaks))

        for pk in peaks:
            A0 = y[pk]
            mu0 = t[pk]
            params0 += [A0, mu0]

    # Ajuste global
    result = least_squares(
        residuals,
        params0,
        args=(all_t, all_y, n_picos_list),
        bounds=(0, np.inf),
        verbose=2
    )

    return result, files, all_t, all_y, n_picos_list

# ============================================================
# 5. Gerar plots e relatório
# ============================================================
def gerar_plots_e_relatorio(result, files, all_t, all_y, n_picos_list, output_dir="resultados"):

    os.makedirs(output_dir, exist_ok=True)

    params = result.x
    k_global, theta_global = params[0], params[1]

    idx = 2
    registros = []

    for file, t, y_exp, n_picos in zip(files, all_t, all_y, n_picos_list):

        nome = os.path.splitext(os.path.basename(file))[0]

        y_sum = np.zeros_like(t)
        picos_individuais = []

        for j in range(n_picos):
            A = params[idx]
            mu = params[idx + 1]
            y_pico = gamma_peak(t, A, mu, k_global, theta_global)

            y_sum += y_pico
            picos_individuais.append((A, mu, y_pico))

            registros.append({
                "arquivo": nome,
                "pico_id": j + 1,
                "A": A,
                "mu": mu,
                "k_global": k_global,
                "theta_global": theta_global
            })

            idx += 2

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(t, y_exp, 'k-', label="Experimental")
        for j, (A, mu, y_pico) in enumerate(picos_individuais):
            plt.plot(t, y_pico, '--', label=f"Pico {j+1}")
        plt.plot(t, y_sum, 'r-', linewidth=2, label="Soma dos picos")

        plt.title(f"Ajuste Gamma — {nome}")
        plt.xlabel("Tempo")
        plt.ylabel("Sinal")
        plt.grid(True, alpha=0.3)
        plt.legend()

        plt.savefig(f"{output_dir}/{nome}_fit.png", dpi=300)
        plt.close()

    # Relatório CSV
    df = pd.DataFrame(registros)
    df.to_csv(f"{output_dir}/relatorio_picos.csv", index=False)

    print("\nPlots salvos em:", output_dir)
    print("Relatório salvo em:", f"{output_dir}/relatorio_picos.csv")

# ============================================================
# 6. Função principal
# ============================================================
def main():

    print("\n>>> Iniciando ajuste global dos cromatogramas de PADRÕES...\n")

    result, files, all_t, all_y, n_picos_list = fit_gamma_variable_peaks(
        "cromatogramas/exp 7_corrida 2/padrões_e7/*.csv"
    )

    gerar_plots_e_relatorio(
        result,
        files,
        all_t,
        all_y,
        n_picos_list,
        output_dir="resultados"
    )

    print("\n>>> Processo concluído com sucesso!\n")

# ============================================================
# Executar script
# ============================================================
if __name__ == "__main__":
    main()
