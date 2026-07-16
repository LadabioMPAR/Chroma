"""Curvas de calibração lineares por analito.

Convenção: y = concentração, x = área  ->  concentração = a * área + b.
Por padrão b = 0 (reta pela origem); há opção de estimar b.

As áreas vêm de um CSV já gerado por outra ferramenta (ajuste_individual ou
analisar), que tenha as colunas `arquivo`, `tempo_pico` e `area`. Casa-se cada
analito ao pico pelo tempo de retenção e cada padrão à sua concentração.
"""

import os
import numpy as np


def fit_linear(x, y, fit_intercept=False):
    """Ajusta y = a*x + b por mínimos quadrados.

    Se `fit_intercept` for False, força b = 0 (reta pela origem).
    Devolve (a, b, r2, n).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)

    if fit_intercept:
        A = np.vstack([x, np.ones_like(x)]).T
        (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    else:
        # y = a*x  ->  a = sum(x*y) / sum(x^2)
        a = float(np.sum(x * y) / np.sum(x * x))
        b = 0.0

    y_pred = a * x + b
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan
    return float(a), float(b), float(r2), int(n)


def save_txt(path, registros):
    """Grava as curvas num .txt tab-delimitado, para outro script consumir.

    Colunas: analito, tempo_pico, a, b, R2, n_pontos.
    Modelo de cada curva: concentracao = a * area + b.
    Fácil de ler, p.ex.:
        pandas.read_csv(path, sep="\\t", comment="#",
                        names=["analito","tempo_pico","a","b","R2","n_pontos"])
    """
    header = [
        "# Curvas de calibracao (Chroma)",
        "# modelo: concentracao = a * area + b",
        "# colunas (separadas por TAB): analito\ttempo_pico\ta\tb\tR2\tn_pontos",
    ]
    lines = list(header)
    for r in registros:
        lines.append(
            f"{r['analito']}\t{r['tempo_pico']}\t"
            f"{r['a_slope']:.10g}\t{r['b_intercept']:.10g}\t"
            f"{r['R2']:.10g}\t{r['n_pontos']}"
        )
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def load_curves(path):
    """Lê um calibracao.txt (gerado por save_txt) de volta.

    Devolve uma lista de dicts: {analito, tempo_pico, a, b, R2, n_pontos}.
    Ignora linhas de comentário (começando com '#') e linhas vazias.
    """
    curves = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            analito, tempo_pico, a, b, r2, n = parts[:6]
            curves.append({
                "analito": analito,
                "tempo_pico": float(tempo_pico),
                "a": float(a),
                "b": float(b),
                "R2": float(r2),
                "n_pontos": int(n),
            })
    return curves


def apply_curve(area, a, b):
    """Concentração a partir da área: conc = a * área + b."""
    return a * area + b


def _same_file(a, b):
    """Compara nomes de arquivo pelo basename sem extensão (ignora caixa)."""
    na = os.path.splitext(os.path.basename(str(a)))[0].lower()
    nb = os.path.splitext(os.path.basename(str(b)))[0].lower()
    return na == nb


def match_area(areas_df, arquivo, peak_time, tolerance):
    """Área do pico de `arquivo` mais próximo de `peak_time` (dentro de
    `tolerance`). Devolve (area, erro): area=None e mensagem se não achar.
    """
    sub = areas_df[areas_df["arquivo"].apply(lambda s: _same_file(s, arquivo))]
    if sub.empty:
        return None, "arquivo não encontrado no CSV de áreas"

    sub = sub.copy()
    sub["_dt"] = (sub["tempo_pico"].astype(float) - peak_time).abs()
    sub = sub[sub["_dt"] <= tolerance]
    if sub.empty:
        return None, f"nenhum pico a menos de {tolerance} de t={peak_time}"

    row = sub.loc[sub["_dt"].idxmin()]
    area = float(row["area"])
    if np.isnan(area):
        return None, "pico casado tem área NaN (ajuste falhou)"
    return area, None
