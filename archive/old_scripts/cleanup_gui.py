#!/usr/bin/env python3
"""
GUI para limpeza dos dados e arquivos gerados do projeto Chroma.
"""

import os
import shutil
import glob
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tqdm import tqdm
import threading

class CleanupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chroma Cleanup Tool")
        self.root.geometry("500x650")
        
        # Variáveis para os checkboxes
        self.var_raw_data = tk.BooleanVar()
        self.var_cromatogramas = tk.BooleanVar()
        self.var_plots = tk.BooleanVar()
        self.var_resumo = tk.BooleanVar()
        self.var_combined = tk.BooleanVar()
        self.var_cdf_files = tk.BooleanVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Título
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(title_frame, text="Chroma Cleanup Tool", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Selecione o que deseja limpar:", 
                                  font=("Arial", 10))
        subtitle_label.pack()
        
        # Frame para checkboxes
        checkbox_frame = ttk.LabelFrame(self.root, text="Opcoes de Limpeza", padding=15)
        checkbox_frame.pack(pady=10, padx=20, fill="x")
        
        # Checkboxes
        ttk.Checkbutton(checkbox_frame, text="[RAW] raw_data/ (dados brutos)", 
                       variable=self.var_raw_data).pack(anchor="w", pady=5)
        
        ttk.Checkbutton(checkbox_frame, text="[CSV] cromatogramas/ (arquivos CSV gerados)", 
                       variable=self.var_cromatogramas).pack(anchor="w", pady=5)
        
        ttk.Checkbutton(checkbox_frame, text="[PNG] plots/ (graficos PNG gerados)", 
                       variable=self.var_plots).pack(anchor="w", pady=5)
        
        ttk.Checkbutton(checkbox_frame, text="[FILE] resumo.csv (arquivo de resumo)", 
                       variable=self.var_resumo).pack(anchor="w", pady=5)
        
        ttk.Checkbutton(checkbox_frame, text="[COMBINED] arquivos CSV compilados", 
                       variable=self.var_combined).pack(anchor="w", pady=5)
        
        ttk.Checkbutton(checkbox_frame, text="[CDF] arquivos .cdf na raiz", 
                       variable=self.var_cdf_files).pack(anchor="w", pady=5)
        
        # Botões de seleção rápida
        quick_frame = ttk.Frame(self.root)
        quick_frame.pack(pady=10)
        
        ttk.Button(quick_frame, text="Selecionar Tudo", 
                  command=self.select_all).pack(side="left", padx=5)
        
        ttk.Button(quick_frame, text="Limpar Selecao", 
                  command=self.clear_selection).pack(side="left", padx=5)
        
        # Botões principais
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.cleanup_button = ttk.Button(button_frame, text="Executar Limpeza", 
                                        command=self.start_cleanup, 
                                        style="Accent.TButton")
        self.cleanup_button.pack(side="left", padx=10)
        
        ttk.Button(button_frame, text="Cancelar", 
                  command=self.root.quit).pack(side="left", padx=10)
        
        # Barra de progresso
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(pady=10, padx=20, fill="x")
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", pady=5)
        
        # Área de log
        log_frame = ttk.LabelFrame(self.root, text="Log de Atividades", padding=10)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=60)
        self.log_text.pack(fill="both", expand=True)
        
    def select_all(self):
        """Seleciona todas as opções."""
        self.var_raw_data.set(True)
        self.var_cromatogramas.set(True)
        self.var_plots.set(True)
        self.var_resumo.set(True)
        self.var_combined.set(True)
        self.var_cdf_files.set(True)
        
    def clear_selection(self):
        """Limpa todas as seleções."""
        self.var_raw_data.set(False)
        self.var_cromatogramas.set(False)
        self.var_plots.set(False)
        self.var_resumo.set(False)
        self.var_combined.set(False)
        self.var_cdf_files.set(False)
        
    def log(self, message):
        """Adiciona mensagem ao log."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_directory(self, directory_path, description):
        """Remove todos os arquivos de um diretório, mantendo o diretório."""
        if os.path.exists(directory_path):
            files_and_dirs = os.listdir(directory_path)
            if files_and_dirs:
                self.log(f"[CLEAN] Limpando {description}...")
                removed_count = 0
                for filename in files_and_dirs:
                    file_path = os.path.join(directory_path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            removed_count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            removed_count += 1
                    except Exception as e:
                        self.log(f"  [ERROR] Erro ao remover {filename}: {e}")
                self.log(f"[OK] {description} limpo! ({removed_count} itens removidos)")
            else:
                self.log(f"[OK] {description} ja estava vazio!")
        else:
            self.log(f"[WARN] {description} nao existe: {directory_path}")
            
    def remove_file(self, file_path, description):
        """Remove um arquivo específico."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.log(f"[OK] {description} removido!")
            except Exception as e:
                self.log(f"[ERROR] Erro ao remover {description}: {e}")
        else:
            self.log(f"[WARN] {description} nao existe")
            
    def cleanup_cdf_files(self):
        """Remove arquivos .cdf da raiz."""
        cdf_files = glob.glob("*.cdf")
        if cdf_files:
            self.log(f"[CLEAN] Removendo {len(cdf_files)} arquivo(s) .cdf da raiz...")
            removed_count = 0
            for cdf_file in cdf_files:
                try:
                    os.remove(cdf_file)
                    removed_count += 1
                except Exception as e:
                    self.log(f"  [ERROR] Erro ao remover {cdf_file}: {e}")
            self.log(f"[OK] {removed_count} arquivo(s) .cdf removidos!")
        else:
            self.log("[WARN] Nenhum arquivo .cdf encontrado na raiz")
            
    def perform_cleanup(self):
        """Executa a limpeza em thread separada."""
        try:
            self.log("[START] Iniciando limpeza...")
            self.log("=" * 40)
            
            # Verificar se pelo menos uma opção foi selecionada
            if not any([self.var_raw_data.get(), self.var_cromatogramas.get(), 
                       self.var_plots.get(), self.var_resumo.get(), self.var_combined.get(),
                       self.var_cdf_files.get()]):
                self.log("[WARN] Nenhuma opcao selecionada!")
                return
            
            # Executar limpezas selecionadas
            if self.var_raw_data.get():
                self.clear_directory("./raw_data", "Pasta de dados brutos (raw_data)")
                
            if self.var_cromatogramas.get():
                self.clear_directory("./cromatogramas", "Pasta de cromatogramas")
                
            if self.var_plots.get():
                self.clear_directory("./plots", "Pasta de graficos")
                
            if self.var_resumo.get():
                self.remove_file("./resumo.csv", "Arquivo de resumo")
                
            if self.var_combined.get():
                # Remove múltiplos arquivos CSV compilados
                combined_files = ["./cromatogramas_combinados.csv", "./cromatogramas_selecionados.csv"]
                for file_path in combined_files:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            self.log(f"[OK] {os.path.basename(file_path)} removido!")
                        except Exception as e:
                            self.log(f"[ERROR] Erro ao remover {os.path.basename(file_path)}: {e}")
                    else:
                        self.log(f"[WARN] {os.path.basename(file_path)} nao existe")
                
            if self.var_cdf_files.get():
                self.cleanup_cdf_files()
            
            self.log("=" * 40)
            self.log("[SUCCESS] Limpeza concluida com sucesso!")
            self.log("")
            self.log("[INFO] Para usar o projeto novamente:")
            self.log("   1. Coloque arquivos .cdf na pasta raw_data/")
            self.log("   2. Execute: python ler.py")
            
            messagebox.showinfo("Sucesso", "Limpeza concluida com sucesso!")
            
        except Exception as e:
            error_msg = f"Erro durante a limpeza: {e}"
            self.log(f"[ERROR] {error_msg}")
            messagebox.showerror("Erro", error_msg)
        finally:
            # Parar barra de progresso e reabilitar botão
            self.progress_bar.stop()
            self.progress_label.config(text="")
            self.cleanup_button.config(state="normal")
            
    def start_cleanup(self):
        """Inicia a limpeza em thread separada."""
        # Verificar seleções
        if not any([self.var_raw_data.get(), self.var_cromatogramas.get(), 
                   self.var_plots.get(), self.var_resumo.get(), self.var_combined.get(),
                   self.var_cdf_files.get()]):
            messagebox.showwarning("Aviso", "Selecione pelo menos uma opcao para limpar!")
            return
            
        # Confirmar ação
        selected_items = []
        if self.var_raw_data.get(): selected_items.append("raw_data/")
        if self.var_cromatogramas.get(): selected_items.append("cromatogramas/")
        if self.var_plots.get(): selected_items.append("plots/")
        if self.var_resumo.get(): selected_items.append("resumo.csv")
        if self.var_combined.get(): selected_items.append("arquivos CSV compilados")
        if self.var_cdf_files.get(): selected_items.append("arquivos .cdf na raiz")
        
        confirm_msg = f"Tem certeza que deseja limpar:\n\n- " + "\n- ".join(selected_items)
        
        if not messagebox.askyesno("Confirmar Limpeza", confirm_msg):
            return
            
        # Limpar log anterior
        self.log_text.delete(1.0, tk.END)
        
        # Iniciar barra de progresso
        self.progress_label.config(text="Executando limpeza...")
        self.progress_bar.start()
        self.cleanup_button.config(state="disabled")
        
        # Executar limpeza em thread separada
        cleanup_thread = threading.Thread(target=self.perform_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

def main():
    root = tk.Tk()
    app = CleanupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()