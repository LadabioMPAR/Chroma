"""Chroma — biblioteca de integração e cálculo de áreas de cromatogramas HPLC.

As ferramentas em scripts/ são independentes (cada uma faz uma coisa) e
compartilham estes módulos:

    config          leitura do config.toml central e resolução de caminhos
    models          modelos de pico (registro plugável; gamma + gaussian)
    io              leitura de CDF, leitura/escrita de CSV de cromatograma
    peaks           detecção de picos (presets: prominence e relative_height)
    baseline        correção de linha de base (linear e BEADS)
    fitting         ajuste individual por janela (livre ou com parâmetros travados)
    fitting_global  ajuste global compartilhando k e theta (padrões)
    analysis        calibrar (k,theta) + analisar amostras travadas
    calibration     curvas de calibração lineares por analito
    plotting        gráficos de cromatograma, ajuste, resíduos, baseline e calibração
"""

from . import (
    config, models, io, peaks, baseline,
    fitting, fitting_global, analysis, calibration, plotting,
)

__all__ = [
    "config", "models", "io", "peaks", "baseline",
    "fitting", "fitting_global", "analysis", "calibration", "plotting",
]
