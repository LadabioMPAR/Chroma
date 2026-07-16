import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from hplc.io import load_chromatogram
from scipy.integrate import simpson
from scipy.stats import linregress
import os

# =================================================================================
# --- PAINEL DE CONTROLE GERAL ---
# =================================================================================

# 1. Pastas
PASTA_CROMATOGRAMAS = 'cromatogramas'
PASTA_SAIDA_GERAL = 'analise_celobiose_final'

# 2. Parâmetros de Análise
LIMITES_INTEGRACAO = {'inicio': 7.6, 'fim': 8.3}
UNIDADE_CONCENTRACAO = 'g/L'
MODO_LINHA_BASE = 'dois_pontos'
PONTOS_LINHA_BASE = {'inicio': 5.0, 'fim': 25.0}
ALTURA_LINHA_BASE_HORIZONTAL = 0.0

# 3. Padrões de Calibração
PADROES_CALIBRACAO = {
    'DCS_Celobiose_2gL_5uL.csv': 0.125, 'DCS_Celobiose_2gL_10uL.csv': 0.25,
    'DCS_Celobiose_2gL_20uL.csv': 0.5, 'DCS_Celobiose_2gL_40uL.csv': 1.0
}

# 4. --- NOVO: PAINEL DE CONTROLE DOS GRÁFICOS ---
CONFIG_GRAFICOS = {
    'geral': {
        'salvar_dpi': 150  # Qualidade da imagem salva (dots per inch)
    },
    'calibracao': {
        'figsize': (10, 7),
        'titulo': 'Curva de Calibração - Celobiose',
        'label_x': f'Concentração ({UNIDADE_CONCENTRACAO})',
        'label_y': 'Área do Pico',
        'cor_pontos': 'red',
        'tamanho_pontos': 8,
        'cor_linha_regressao': 'firebrick',
        'estilo_linha_regressao': '-',
        'cor_caixa_texto': 'wheat'
    },
    'amostras': {
        'figsize': (12, 7),
        'titulo_base': 'Integração',
        'label_x': 'Tempo (min)',
        'label_y': 'Sinal (mAU)',
        'cor_sinal_total': '#CCCCCC', # Cinza claro
        'cor_pico_janela': 'black',
        'cor_linha_base': 'red',
        'estilo_linha_base': '--',
        'cor_area': 'skyblue',
        'transparencia_area': 0.6,
        'cor_limites': 'purple',
        'estilo_limites': '--',
        'cor_pontos_base': 'red',
        'estilo_pontos_base': 'X',
        'tamanho_pontos_base': 5
    }
}
# =================================================================================

def processar_pico(df, limites_integracao, modo_base, **kwargs):
    # (Esta função permanece inalterada)
    df_pico = df[(df['time'] >= limites_integracao['inicio']) & (df['time'] <= limites_integracao['fim'])]
    if df_pico.empty: return None, None, None, None
    x_pico, y_pico = df_pico['time'].values, df_pico['signal'].values
    linha_de_base_valores = np.zeros_like(y_pico)
    pontos_base_plot = None
    if modo_base == 'horizontal':
        altura_base = kwargs.get('altura_base_horizontal', 0.0)
        linha_de_base_valores = np.full_like(y_pico, altura_base)
    elif modo_base == 'dois_pontos':
        pontos_base_req = kwargs.get('pontos_base', {})
        t1_base, t2_base = pontos_base_req.get('inicio'), pontos_base_req.get('fim')
        p1 = df.iloc[np.abs(df['time'] - t1_base).argmin()]
        p2 = df.iloc[np.abs(df['time'] - t2_base).argmin()]
        t1, y1, t2, y2 = p1['time'], p1['signal'], p2['time'], p2['signal']
        m = (y2 - y1) / (t2 - t1) if (t2 - t1) != 0 else 0
        c = y1 - m * t1
        linha_de_base_valores = m * x_pico + c
        pontos_base_plot = {'t': [t1, t2], 'y': [y1, y2]}
    sinal_corrigido = y_pico - linha_de_base_valores
    sinal_corrigido[sinal_corrigido < 0] = 0
    area = simpson(sinal_corrigido, x_pico)
    return area, x_pico, y_pico, linha_de_base_valores, pontos_base_plot

def main():
    sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})
    pasta_plots_amostras = os.path.join(PASTA_SAIDA_GERAL, 'plots_amostras')
    pasta_calibracao = os.path.join(PASTA_SAIDA_GERAL, 'calibracao')
    for pasta in [PASTA_SAIDA_GERAL, pasta_plots_amostras, pasta_calibracao]:
        os.makedirs(pasta, exist_ok=True)
    
    print("\n--- Etapa 1: Geração da Curva de Calibração ---")
    dados_curva = []
    # (Loop da calibração permanece o mesmo)
    for nome_arquivo, concentracao in PADROES_CALIBRACAO.items():
        caminho_completo = os.path.join(PASTA_CROMATOGRAMAS, nome_arquivo)
        try:
            df = load_chromatogram(caminho_completo, cols=['time', 'signal'])
            area, _, _, _, _ = processar_pico(df, LIMITES_INTEGRACAO, MODO_LINHA_BASE, altura_base_horizontal=ALTURA_LINHA_BASE_HORIZONTAL, pontos_base=PONTOS_LINHA_BASE)
            if area is not None: dados_curva.append({'arquivo': nome_arquivo, 'concentracao': concentracao, 'area': area})
        except Exception as e: print(f"     ERRO no padrão {nome_arquivo}: {e}")

    if len(dados_curva) < 2: print("\nERRO CRÍTICO: Calibração falhou."); return
    df_curva = pd.DataFrame(dados_curva)
    slope, intercept, r_value, _, _ = linregress(df_curva['concentracao'], df_curva['area'])
    r_squared = r_value**2
    
    print("  -> Salvando relatório e gráfico da calibração...")
    caminho_relatorio_calibracao = os.path.join(pasta_calibracao, 'relatorio_calibracao.txt')
    with open(caminho_relatorio_calibracao, 'w') as f:
        f.write(f"--- Relatório da Curva de Calibração ---\n\nModo da Linha de Base: {MODO_LINHA_BASE}\n\n")
        f.write(f"Equação da Reta: Área = {slope:.4f} * Concentração + {intercept:.4f}\n")
        f.write(f"Coeficiente de Determinação (R²): {r_squared:.6f}\n\nDados utilizados:\n")
        f.write(df_curva.to_string(index=False))
    
    # Plotagem da calibração usando o dicionário de configuração
    cfg_cal = CONFIG_GRAFICOS['calibracao']
    plt.figure(figsize=cfg_cal['figsize'])
    plt.plot(df_curva['concentracao'], df_curva['area'], 'o', color=cfg_cal['cor_pontos'], markersize=cfg_cal['tamanho_pontos'], label='Padrões')
    x_fit = np.array([0] + list(df_curva['concentracao']))
    y_fit = slope * x_fit + intercept
    plt.plot(x_fit, y_fit, linestyle=cfg_cal['estilo_linha_regressao'], color=cfg_cal['cor_linha_regressao'], label='Linha de Regressão')
    texto_legenda = f'Área = {slope:.2f} * C + {intercept:.2f}\n$R^2$ = {r_squared:.4f}'
    plt.text(0.05, 0.95, texto_legenda, transform=plt.gca().transAxes, fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc=cfg_cal['cor_caixa_texto'], alpha=0.5))
    plt.title(cfg_cal['titulo']); plt.xlabel(cfg_cal['label_x']); plt.ylabel(cfg_cal['label_y']); plt.legend(); 
    caminho_plot_calibracao = os.path.join(pasta_calibracao, 'curva_calibracao.png')
    plt.savefig(caminho_plot_calibracao, dpi=CONFIG_GRAFICOS['geral']['salvar_dpi'])
    plt.close()

    print("\n--- Etapa 2: Processamento em Lote das Amostras ---")
    todos_os_resultados = []
    cfg_amostra = CONFIG_GRAFICOS['amostras']
    for nome_arquivo in sorted(os.listdir(PASTA_CROMATOGRAMAS)):
        if nome_arquivo.lower().endswith('.csv'):
            caminho_completo = os.path.join(PASTA_CROMATOGRAMAS, nome_arquivo)
            print(f"  -> Processando amostra: {nome_arquivo}")
            try:
                df = load_chromatogram(caminho_completo, cols=['time', 'signal'])
                area_calculada, x_pico, y_pico, linha_de_base_valores, pontos_base_plot = processar_pico(df, LIMITES_INTEGRACAO, MODO_LINHA_BASE, altura_base_horizontal=ALTURA_LINHA_BASE_HORIZONTAL, pontos_base=PONTOS_LINHA_BASE)
                if area_calculada is None: continue
                concentracao_calculada = (area_calculada - intercept) / slope if slope != 0 else 0
                if concentracao_calculada < 0: concentracao_calculada = 0
                todos_os_resultados.append({'Nome do Arquivo': nome_arquivo, 'Área Calculada': area_calculada, 'Concentração Calculada': concentracao_calculada})
                
                # Plotagem das amostras usando o dicionário de configuração
                plt.figure(figsize=cfg_amostra['figsize'])
                plt.plot(df['time'], df['signal'], color=cfg_amostra['cor_sinal_total'], alpha=0.7, label='Sinal Completo')
                plt.plot(x_pico, y_pico, 'o-', color=cfg_amostra['cor_pico_janela'], label='Dados do Pico', markersize=3)
                plt.plot(x_pico, linha_de_base_valores, linestyle=cfg_amostra['estilo_linha_base'], color=cfg_amostra['cor_linha_base'], label=f'Linha de Base ({MODO_LINHA_BASE})')
                if MODO_LINHA_BASE == 'dois_pontos' and pontos_base_plot:
                    plt.plot(pontos_base_plot['t'], pontos_base_plot['y'], cfg_amostra['estilo_pontos_base'], color=cfg_amostra['cor_pontos_base'], markersize=cfg_amostra['tamanho_pontos_base'], label='Pontos da Base')
                plt.fill_between(x_pico, y_pico, linha_de_base_valores, where=y_pico > linha_de_base_valores, color=cfg_amostra['cor_area'], alpha=cfg_amostra['transparencia_area'], label=f'Área = {area_calculada:.2f}')
                plt.axvline(x=LIMITES_INTEGRACAO['inicio'], color=cfg_amostra['cor_limites'], linestyle=cfg_amostra['estilo_limites'], label='Limites de Integração')
                plt.axvline(x=LIMITES_INTEGRACAO['fim'], color=cfg_amostra['cor_limites'], linestyle=cfg_amostra['estilo_limites'])
                titulo_grafico = f"{cfg_amostra['titulo_base']} - {nome_arquivo}\nConcentração: {concentracao_calculada:.4f} {UNIDADE_CONCENTRACAO}"
                plt.title(titulo_grafico)
                plt.xlabel(cfg_amostra['label_x']); plt.ylabel(cfg_amostra['label_y']); plt.legend(); 
                nome_base = os.path.splitext(nome_arquivo)[0]
                caminho_saida_plot = os.path.join(pasta_plots_amostras, f"{nome_base}_integracao.png")
                plt.savefig(caminho_saida_plot, dpi=CONFIG_GRAFICOS['geral']['salvar_dpi'])
                plt.close()
            except Exception as e: print(f"     ERRO: {e}")
            
    if todos_os_resultados:
        df_resultados = pd.DataFrame(todos_os_resultados)
        caminho_saida_csv = os.path.join(PASTA_SAIDA_GERAL, 'resultados_finais_celobiose.csv')
        df_resultados.to_csv(caminho_saida_csv, index=False, sep=';', decimal=',')
        print(f"\n✅ Processamento concluído!")
        print(f"  -> Resultados numéricos salvos em: '{caminho_saida_csv}'")
        print(f"  -> Gráficos de verificação salvos em: '{pasta_plots_amostras}'")
        print(f"  -> Detalhes da calibração salvos em: '{pasta_calibracao}'")

if __name__ == '__main__':
    main()