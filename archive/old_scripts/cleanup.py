#!/usr/bin/env python3
"""
Script para limpar os dados e arquivos gerados do projeto Chroma.
"""

import os
import shutil
import glob
from tqdm import tqdm

def clear_directory(directory_path, description):
    """Remove todos os arquivos de um diretório, mantendo o diretório."""
    if os.path.exists(directory_path):
        files_and_dirs = os.listdir(directory_path)
        if files_and_dirs:
            # Remove todos os arquivos e subdiretórios com barra de progresso
            for filename in tqdm(files_and_dirs, desc=f"Limpando {description}", unit="item"):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    tqdm.write(f"  ❌ Erro ao remover {filename}: {e}")
            print(f"✅ {description} limpo!")
        else:
            print(f"✅ {description} já estava vazio!")
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

def show_menu():
    """Mostra o menu de opções de limpeza."""
    print("🧹 MENU DE LIMPEZA - Projeto Chroma")
    print("=" * 40)
    print("Escolha o que deseja limpar:")
    print()
    print("1. 📁 raw_data/ (dados brutos)")
    print("2. 📊 cromatogramas/ (arquivos CSV gerados)")
    print("3. 📈 plots/ (gráficos PNG gerados)")
    print("4. 📄 resumo.csv (arquivo de resumo)")
    print("5. 🗑️  arquivos .cdf na raiz")
    print("6. 🔥 TUDO (limpeza completa)")
    print("0. ❌ Cancelar")
    print()

def get_user_choices():
    """Obtém as escolhas do usuário."""
    while True:
        choice = input("Digite sua escolha (ex: 1,3,4 ou 6 para tudo): ").strip()
        
        if choice == "0":
            print("❌ Operação cancelada.")
            return None
        
        if choice == "6":
            return [1, 2, 3, 4, 5]  # Todas as opções
        
        try:
            choices = [int(x.strip()) for x in choice.split(",")]
            # Validar se todas as escolhas estão no range válido
            if all(1 <= c <= 5 for c in choices):
                return sorted(list(set(choices)))  # Remove duplicatas e ordena
            else:
                print("❌ Escolhas inválidas. Use números de 1 a 6.")
        except ValueError:
            print("❌ Formato inválido. Use números separados por vírgula (ex: 1,3,4).")

def main():
    show_menu()
    choices = get_user_choices()
    
    if choices is None:
        return
    
    print(f"\n🧹 Iniciando limpeza selecionada...\n")
    
    # Mapear escolhas para ações
    actions = {
        1: ("./raw_data", "Pasta de dados brutos (raw_data)"),
        2: ("./cromatogramas", "Pasta de cromatogramas"),
        3: ("./plots", "Pasta de gráficos"),
        4: ("./resumo.csv", "Arquivo de resumo"),
        5: ("*.cdf", "Arquivos .cdf na raiz")
    }
    
    # Executar limpezas selecionadas
    for choice in choices:
        if choice in [1, 2, 3]:  # Diretórios
            dir_path, description = actions[choice]
            clear_directory(dir_path, description)
            print()
        elif choice == 4:  # Arquivo de resumo
            file_path, description = actions[choice]
            remove_file(file_path, description)
            print()
        elif choice == 5:  # Arquivos .cdf
            cdf_files = glob.glob("*.cdf")
            if cdf_files:
                print("📁 Arquivos .cdf encontrados na raiz do projeto:")
                for cdf_file in tqdm(cdf_files, desc="Removendo arquivos CDF", unit="arquivo"):
                    try:
                        os.remove(cdf_file)
                    except Exception as e:
                        tqdm.write(f"  ❌ Erro ao remover {cdf_file}: {e}")
                print("✅ Arquivos .cdf removidos!")
                print()
            else:
                print("⚠️  Nenhum arquivo .cdf encontrado na raiz.")
                print()
    
    print("🎉 Limpeza concluída!")
    print("\n💡 Dica: Para usar o projeto novamente:")
    print("   1. Coloque seus arquivos .cdf na pasta raw_data/")
    print("   2. Execute: python ler.py")

if __name__ == "__main__":
    main()