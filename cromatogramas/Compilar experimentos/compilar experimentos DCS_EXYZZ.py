import pandas as pd
import re
import glob
import os
from collections import defaultdict


def extract_info_dcs(filename):
    """
    Extrai informações do nome do arquivo no formato DCS_EXYZZ
    X = número do experimento
    Y = número da replicata
    ZZ = número da amostra
    """
    basename = os.path.basename(filename)
    match = re.match(r'DCS_E(\d)(\d)(\d{2})\.csv', basename)
    if match:
        experimento = match.group(1)
        replicata = match.group(2)
        amostra = match.group(3)
        return experimento, replicata, amostra
    return None, None, None


def buscar_arquivos_dcs(num_experimento, diretorio_base='.'):
    """
    Busca automaticamente todos os arquivos CSV no formato DCS_EXYZZ na pasta EXP X
    """
    # Construir o caminho da pasta do experimento
    pasta_experimento = os.path.join(diretorio_base, f'EXP {num_experimento}')

    # Verificar se a pasta existe
    if not os.path.exists(pasta_experimento):
        print(f"⚠ Pasta não encontrada: {pasta_experimento}")
        return []

    # Buscar todos os arquivos CSV que seguem o padrão DCS_EXYZZ dentro da pasta
    pattern = os.path.join(pasta_experimento, f'DCS_E{num_experimento}[0-9][0-9][0-9].csv')
    files = glob.glob(pattern)

    if not files:
        print(f"⚠ Nenhum arquivo encontrado no padrão DCS_E{num_experimento}YZZ.csv na pasta: {pasta_experimento}")
        return []

    print(f"✓ {len(files)} arquivo(s) encontrado(s) na pasta '{pasta_experimento}':")
    for f in sorted(files):
        exp, rep, amo = extract_info_dcs(f)
        print(f"  - {os.path.basename(f)} -> Exp: {exp}, Rep: {rep}, Amostra: {amo}")

    return files


def juntar_cromatogramas_dcs(file_list):
    """
    Junta todos os cromatogramas em um único DataFrame
    Mantém apenas as colunas 'time' e 'signal'
    """
    all_data = []

    for file in sorted(file_list):
        # Ler o arquivo CSV
        df = pd.read_csv(file)

        # Manter apenas as colunas time e signal
        if 'time' in df.columns and 'signal' in df.columns:
            df_clean = df[['time', 'signal']].copy()
            all_data.append(df_clean)
        else:
            print(f"⚠ Aviso: Arquivo {os.path.basename(file)} não contém colunas 'time' e 'signal'")

    # Concatenar todos os DataFrames
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        return result
    else:
        return pd.DataFrame(columns=['time', 'signal'])


def processar_experimento_dcs(num_experimento, diretorio_base='.'):
    """
    Processa um experimento específico (arquivos DCS)
    """
    print("=" * 60)
    print("PROCESSAMENTO DE CROMATOGRAMAS DCS")
    print("=" * 60)
    print(f"\nExperimento selecionado: {num_experimento}")
    print(f"Procurando arquivos DCS na pasta 'EXP {num_experimento}'...")
    print("─" * 60)

    # Buscar automaticamente todos os arquivos na pasta do experimento
    files = buscar_arquivos_dcs(num_experimento, diretorio_base)

    if files:
        print(f"\n{'─' * 60}")
        print(f"Processando Experimento {num_experimento}...")
        print(f"  Total de arquivos encontrados: {len(files)}")

        df_combined = juntar_cromatogramas_dcs(files)
        output_filename = f'Experimento_{num_experimento}_completo.csv'
        df_combined.to_csv(output_filename, index=False)

        print(f"\n  ✓ Arquivo salvo: {output_filename}")
        print(f"  ✓ Total de linhas: {len(df_combined):,}")
        print(f"  ✓ Colunas: {list(df_combined.columns)}")

        print(f"\n{'=' * 60}")
        print("✓ PROCESSAMENTO CONCLUÍDO!")
        print(f"{'=' * 60}")
    else:
        print("\n⚠ Nenhum arquivo para processar.")
        print("Verifique se:")
        print(f"  1. A pasta 'EXP {num_experimento}' existe")
        print(f"  2. Existem arquivos CSV no formato DCS_E{num_experimento}YZZ.csv dentro da pasta")


# ========== EXECUÇÃO ==========

# Para processar o experimento, defina o número e execute:
num_experimento = '6'  # ← ALTERE AQUI O NÚMERO DO EXPERIMENTO
processar_experimento_dcs(num_experimento)
