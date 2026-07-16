import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import os

# --- BEADS BASELINE ---
def beads_baseline(y, lam=3e5, fc=0.01, r=0.5, nit=60):
    N = len(y)
    D = np.diff(np.eye(N), 2, axis=0)
    H = lam * (D.T @ D)

    win = int(max(5, int(fc * N)))
    if win % 2 == 0:
        win += 1

    z = y.copy()
    w = np.ones(N)

    for _ in range(nit):
        W = np.diag(w)
        z = np.linalg.solve(W + H, w * y)
        z = savgol_filter(z, win, 3)
        d = y - z
        w = 1 / (1 + (d / r) ** 2)

    return z


# ============================================
# PROCESSAR VÁRIOS ARQUIVOS
# ============================================

nomes = [
    "CRA14_F2",
    "CRA14_F44",
    "CRA14_F49",
    "CRA14_F51",
    "CRA14_F54",
    "CRA14_F55",
    "CRA14_F56",
    "CRA14_F58",
    "CRA14_F59"
]

pasta = "cromatogramas/Wilhamis_CRA14_XOS/"   # ajuste se necessário

for nome in nomes:
    filepath = os.path.join(pasta, f"{nome}.csv")

    if not os.path.exists(filepath):
        print(f"[AVISO] Arquivo não encontrado: {filepath}")
        continue

    print("Processando:", filepath)

    # Ler
    df = pd.read_csv(filepath, header=None)
    df[0] = pd.to_numeric(df[0], errors="coerce")
    df[1] = pd.to_numeric(df[1], errors="coerce")
    df = df.dropna().reset_index(drop=True)

    t = df[0].to_numpy()
    y = df[1].to_numpy()

    # Corrigir baseline
    baseline = beads_baseline(y, lam=1e6, fc=0.015, r=0.05, nit=80)
    corr = y - baseline

    # Salvar CSV
    out = pd.DataFrame({"time": t, "signal": y, "baseline": baseline, "corrected": corr})
    out_csv = os.path.join(pasta, f"{nome}_BEADS.csv")
    out.to_csv(out_csv, index=False)
    print("Salvo:", out_csv)

    # Plot
    plt.figure(figsize=(12,6))
    plt.plot(t, y, label="Original", alpha=0.6)
    plt.plot(t, baseline, label="Baseline (BEADS)", linewidth=2)
    plt.plot(t, corr, label="Corrigido", linewidth=1)
    plt.legend()
    plt.title(f"Correção de linha de base - {nome}")
    out_png = os.path.join(pasta, f"{nome}_BEADS.png")
    plt.savefig(out_png, dpi=300)
    plt.close()
    print("Imagem salva:", out_png)

print("\n✔️ Finalizado!")
