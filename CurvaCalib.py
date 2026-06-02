"""
Curva de calibração e estimativa de concentração para amostras ESTR.

Arquivos de entrada:
  - resultados/ESTR/resultados.csv       : amostras (arquivo,pico,tempo_pico,A,k,theta)
  - resultados/ESTR/relatorio_picos.csv  : padrões  (arquivo,pico_id,A,mu,k_global,theta_global)

Saída:
  - resultados/ESTR/concentracoes_estimadas.csv
  - resultados/ESTR/curvas_calibracao.png
"""

import re
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# ──────────────────────────────────────────────────────────────────────────────
# PARÂMETROS
# ──────────────────────────────────────────────────────────────────────────────

PASTA        = os.path.join("resultados", "ESTR")
ARQ_AMOSTRAS = os.path.join(PASTA, "resultados.csv")
ARQ_PADROES  = os.path.join(PASTA, "relatorio_picos.csv")
ARQ_SAIDA    = os.path.join(PASTA, "concentracoes_estimadas.csv")
ARQ_FIGURA   = os.path.join(PASTA, "curvas_calibracao.png")

# Tolerância (em unidades de tempo_pico / mu) para considerar o mesmo analito
TOLERANCIA_TEMPO = 0.5   # ajuste conforme a escala dos seus dados

# ──────────────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ──────────────────────────────────────────────────────────────────────────────

def parse_nome_amostra(nome: str):
    """
    Extrai (amostra, replica) do nome do arquivo de resultados.
    Ex.: 'ESTR-1-1' → amostra=-1, replica=1
         'ESTR0-1'  → amostra=0,  replica=1
         'ESTR1-2'  → amostra=1,  replica=2
    """
    m = re.match(r"ESTR(-?\d+)-(\d+)", nome)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def parse_padrao(nome: str):
    """
    Extrai (analito, concentração_g_L) do nome do arquivo padrão.
    A concentração nominal (20 µL) é multiplicada por fator de volume:
      5 µL  → × 0.25
      10 µL → × 0.5
      20 µL → × 1.0
      40 µL → × 2.0

    Retorna None se não for um padrão de analito (ex.: AGUA).
    """
    # Ex.: "Celobiose 0.5gl_20ul" ou "Glicose 2gl_10ul"
    m = re.match(
        r"(Celobiose|Glicose|Xilose)\s+([\d.]+)gl_([\d]+)ul",
        nome,
        re.IGNORECASE,
    )
    if not m:
        return None, None

    analito      = m.group(1).capitalize()
    conc_nominal = float(m.group(2))   # concentração a 20 µL
    volume_ul    = int(m.group(3))

    fator = volume_ul / 20.0
    conc  = conc_nominal * fator
    return analito, conc


# ──────────────────────────────────────────────────────────────────────────────
# 1. LEITURA DOS DADOS
# ──────────────────────────────────────────────────────────────────────────────

print("Lendo arquivos...")
df_amostras = pd.read_csv(ARQ_AMOSTRAS)
df_padroes  = pd.read_csv(ARQ_PADROES)

# Colunas esperadas
# amostras : arquivo, pico, tempo_pico, A, k, theta
# padrões  : arquivo, pico_id, A, mu, k_global, theta_global

# Renomeia para uniformizar a coluna de tempo de pico
df_padroes = df_padroes.rename(columns={"mu": "tempo_pico"})

print(f"  Amostras : {len(df_amostras)} linhas")
print(f"  Padrões  : {len(df_padroes)} linhas")

# ──────────────────────────────────────────────────────────────────────────────
# 2. METADADOS DOS PADRÕES
# ──────────────────────────────────────────────────────────────────────────────

df_padroes[["analito", "concentracao"]] = df_padroes["arquivo"].apply(
    lambda x: pd.Series(parse_padrao(x))
)

# Remove linhas sem analito identificado (AGUA, etc.)
df_padroes_analito = df_padroes.dropna(subset=["analito"]).copy()

analitos = df_padroes_analito["analito"].unique()
print(f"\nAnalitos encontrados nos padrões: {list(analitos)}")

# ──────────────────────────────────────────────────────────────────────────────
# 3. METADADOS DAS AMOSTRAS
# ──────────────────────────────────────────────────────────────────────────────

df_amostras[["nivel_amostra", "replica"]] = df_amostras["arquivo"].apply(
    lambda x: pd.Series(parse_nome_amostra(x))
)

# ──────────────────────────────────────────────────────────────────────────────
# 4. ASSOCIAÇÃO DE PICOS POR TEMPO (amostras ↔ padrões)
# ──────────────────────────────────────────────────────────────────────────────

def associar_analito(tempo_amostra, df_padroes_analito, tol):
    """
    Dado o tempo de um pico na amostra, encontra o analito cujo tempo médio
    nos padrões é mais próximo, dentro da tolerância.
    """
    tempos_medios = (
        df_padroes_analito.groupby("analito")["tempo_pico"]
        .mean()
        .reset_index()
        .rename(columns={"tempo_pico": "tempo_medio"})
    )
    tempos_medios["diff"] = (tempos_medios["tempo_medio"] - tempo_amostra).abs()
    candidato = tempos_medios.loc[tempos_medios["diff"].idxmin()]
    if candidato["diff"] <= tol:
        return candidato["analito"], candidato["tempo_medio"]
    return None, None


df_amostras[["analito_assoc", "tempo_medio_padrao"]] = df_amostras["tempo_pico"].apply(
    lambda t: pd.Series(associar_analito(t, df_padroes_analito, TOLERANCIA_TEMPO))
)

nao_assoc = df_amostras["analito_assoc"].isna().sum()
print(f"\nPicos das amostras sem associação (fora da tolerância {TOLERANCIA_TEMPO}): {nao_assoc}")

# ──────────────────────────────────────────────────────────────────────────────
# 5. CURVA DE CALIBRAÇÃO (regressão linear: A = a·C + b)
# ──────────────────────────────────────────────────────────────────────────────

modelos = {}   # analito → (slope, intercept, r²)

fig, axes = plt.subplots(1, len(analitos), figsize=(5 * len(analitos), 5))
if len(analitos) == 1:
    axes = [axes]

for ax, analito in zip(axes, sorted(analitos)):
    sub = df_padroes_analito[df_padroes_analito["analito"] == analito].copy()

    # Agrupa por concentração (média da área entre réplicas/volumes equivalentes)
    cal = sub.groupby("concentracao")["A"].mean().reset_index()
    cal = cal.sort_values("concentracao")

    if len(cal) < 2:
        print(f"  [{analito}] poucos pontos de calibração ({len(cal)}), pulando.")
        continue

    slope, intercept, r, p, se = stats.linregress(cal["concentracao"], cal["A"])
    r2 = r ** 2
    modelos[analito] = (slope, intercept, r2)

    print(f"\n  [{analito}] Calibração: A = {slope:.4f}·C + {intercept:.4f}  |  R² = {r2:.4f}")

    # Gráfico
    c_fit = np.linspace(cal["concentracao"].min(), cal["concentracao"].max(), 200)
    ax.scatter(cal["concentracao"], cal["A"], color="steelblue", zorder=3, label="Padrões")
    ax.plot(c_fit, slope * c_fit + intercept, "r-", label=f"y={slope:.3f}x+{intercept:.3f}\nR²={r2:.4f}")
    ax.set_title(analito)
    ax.set_xlabel("Concentração (g/L)")
    ax.set_ylabel("Área (A)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(ARQ_FIGURA, dpi=150)
plt.close()
print(f"\nFigura salva em: {ARQ_FIGURA}")

# ──────────────────────────────────────────────────────────────────────────────
# 6. ESTIMATIVA DE CONCENTRAÇÃO DAS AMOSTRAS
# ──────────────────────────────────────────────────────────────────────────────

def estimar_concentracao(row, modelos):
    analito = row["analito_assoc"]
    if pd.isna(analito) or analito not in modelos:
        return np.nan
    slope, intercept, _ = modelos[analito]
    if slope == 0:
        return np.nan
    return (row["A"] - intercept) / slope


df_amostras["concentracao_estimada_gL"] = df_amostras.apply(
    lambda r: estimar_concentracao(r, modelos), axis=1
)

# ──────────────────────────────────────────────────────────────────────────────
# 7. SAÍDA
# ──────────────────────────────────────────────────────────────────────────────

colunas_saida = [
    "arquivo", "nivel_amostra", "replica",
    "pico", "tempo_pico",
    "analito_assoc", "tempo_medio_padrao",
    "A", "concentracao_estimada_gL",
]

df_saida = df_amostras[colunas_saida].copy()
df_saida = df_saida.rename(columns={
    "analito_assoc":           "analito",
    "tempo_medio_padrao":      "tempo_pico_padrao",
    "concentracao_estimada_gL": "concentracao_gL",
})

df_saida.to_csv(ARQ_SAIDA, index=False, float_format="%.6f")
print(f"\nResultados salvos em: {ARQ_SAIDA}")

# Resumo por amostra × analito (média entre réplicas)
print("\n─── Resumo: concentração média por nível de amostra ───")
resumo = (
    df_saida.dropna(subset=["concentracao_gL"])
    .groupby(["nivel_amostra", "analito"])["concentracao_gL"]
    .agg(["mean", "std", "count"])
    .rename(columns={"mean": "média (g/L)", "std": "desvio (g/L)", "count": "n"})
    .reset_index()
)
print(resumo.to_string(index=False))