import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

# --- BEADS BASELINE ---
def beads_baseline(y, lam=3e5, fc=0.01, r=0.5, nit=60):
    """
    Implementação simples e estável do BEADS.
    - y: vetor do sinal
    - lam: suavidade da baseline
    - fc: frequência de corte (0.005–0.02 funciona bem)
    - r: parâmetro de robustez
    - nit: iterações
    """
    N = len(y)
    D = np.diff(np.eye(N), 2, axis=0)  # operador derivada 2
    H = lam * (D.T @ D)

    # filtro passa-baixa para atualização 
    win = int(max(5, int(fc * N)))
    if win % 2 == 0:
        win += 1

    z = y.copy()
    w = np.ones(N)

    for _ in range(nit):
        # resolve baseline
        W = np.diag(w)
        z = np.linalg.solve(W + H, w * y)

        # filtra suavemente para evitar oscilações
        z = savgol_filter(z, win, 3)

        # atualiza pesos (robustez)
        d = y - z
        w = 1 / (1 + (d / r) ** 2)

    return z


# ============================================
# Ler arquivo de cromatograma e aplicar BEADS
# ============================================

filepath = r"cromatogramas\exp 7_corrida 2\padrões_e7\clb_05_gl.csv"
print("Lendo:", filepath)

df = pd.read_csv(filepath, header=None)
df[0] = pd.to_numeric(df[0], errors="coerce")
df[1] = pd.to_numeric(df[1], errors="coerce")
df = df.dropna().reset_index(drop=True)

t = df[0].to_numpy()
y = df[1].to_numpy()

# corrigir baseline usando BEADS
baseline = beads_baseline(y, lam=1e6, fc=0.015, r=0.05, nit=80)
corr = y - baseline

# salvar
out = pd.DataFrame({"time": t, "signal": y, "baseline": baseline, "corrected": corr})
out.to_csv("clb_05_gl_BEADS.csv", index=False)
print("Salvo: clb_05_gl_BEADS.csv")

# plotar
plt.figure(figsize=(12,6))
plt.plot(t, y, label="Original", alpha=0.6)
plt.plot(t, baseline, label="Baseline (BEADS)", linewidth=2)
plt.plot(t, corr, label="Corrigido", linewidth=1)
plt.legend()
plt.title("Correção de linha de base - BEADS")
plt.savefig("clb_05_gl_BEADS.png", dpi=300)
plt.show()
