#!/usr/bin/env python3
"""
Script para limpar os dados e arquivos gerados do projeto Chroma.
"""

import os
import shutil
import glob

def clear_directory(directory_path, description):
    """Remove todos os arquivos de um diretório, mantendo o diretório."""
    if os.path.exists(directory_path):
        # Remove todos os arquivos e subdiretórios
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f"  Removido: {filename}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"  Removido diretório: {filename}")
            except Exception as e:
                print(f"  Erro ao remover {filename}: {e}")
        print(f"✅ {description} limpo!")
    else:
        print(f"⚠️  {description} não existe: {directory_path}")

def remove_file(file_path, description):
    """Remove um arquivo específico."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ {description} removido: {file_path}")
        except Exception as e:
            print(f"❌ Erro ao remover {description}: {e}")
    else:
        print(f"⚠️  {description} não existe: {file_path}")

def main():
    print("🧹 Iniciando limpeza dos dados do projeto Chroma...\n")
    
    # Diretórios para limpar
    directories_to_clear = [
        ("./raw_data", "Pasta de dados brutos (raw_data)"),
        ("./cromatogramas", "Pasta de cromatogramas"),
        ("./plots", "Pasta de gráficos")
    ]
    
    # Arquivos para remover
    files_to_remove = [
        ("./resumo.csv", "Arquivo de resumo")
    ]
    
    # Limpar diretórios
    for dir_path, description in directories_to_clear:
        clear_directory(dir_path, description)
        print()
    
    # Remover arquivos específicos
    for file_path, description in files_to_remove:
        remove_file(file_path, description)
        print()
    
    # Procurar e remover outros arquivos .cdf que possam estar soltos
    cdf_files = glob.glob("*.cdf")
    if cdf_files:
        print("📁 Arquivos .cdf encontrados na raiz do projeto:")
        for cdf_file in cdf_files:
            try:
                os.remove(cdf_file)
                print(f"  ✅ Removido: {cdf_file}")
            except Exception as e:
                print(f"  ❌ Erro ao remover {cdf_file}: {e}")
        print()
    
    print("🎉 Limpeza concluída!")
    print("\n💡 Dica: Para usar o projeto novamente:")
    print("   1. Coloque seus arquivos .cdf na pasta raw_data/")
    print("   2. Execute: python ler.py")

if __name__ == "__main__":
    main()