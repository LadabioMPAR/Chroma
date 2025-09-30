#!/usr/bin/env python3
"""
Script para compilar cromatogramas selecionados em um único arquivo CSV.
Permite escolher quais amostras incluir na compilação.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

class ChromatogramCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chroma Compiler - Seletor de Cromatogramas")
        self.root.geometry("700x600")
        
        # Diretórios
        self.chromatograms_dir = "./cromatogramas"
        self.output_file = "cromatogramas_selecionados.csv"
        
        # Lista de arquivos disponíveis
        self.available_files = []
        self.selected_files = []
        
        self.create_widgets()
        self.refresh_file_list()
        
    def create_widgets(self):
        # Título
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(title_frame, text="Chroma Compiler", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Selecione os cromatogramas para compilar", 
                                  font=("Arial", 10))
        subtitle_label.pack()
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Configuração de saída
        config_frame = ttk.LabelFrame(main_frame, text="Configuracao", padding=10)
        config_frame.pack(fill="x", pady=(0, 10))
        
        # Diretório de cromatogramas
        ttk.Label(config_frame, text="Pasta dos cromatogramas:").pack(anchor="w")
        dir_frame = ttk.Frame(config_frame)
        dir_frame.pack(fill="x", pady=(5, 10))
        
        self.dir_var = tk.StringVar(value=self.chromatograms_dir)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, state="readonly")
        self.dir_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(dir_frame, text="Alterar", 
                  command=self.select_directory).pack(side="right", padx=(5, 0))
        
        # Arquivo de saída
        ttk.Label(config_frame, text="Arquivo de saida:").pack(anchor="w")
        output_frame = ttk.Frame(config_frame)
        output_frame.pack(fill="x", pady=5)
        
        self.output_var = tk.StringVar(value=self.output_file)
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(output_frame, text="Escolher", 
                  command=self.select_output_file).pack(side="right", padx=(5, 0))
        
        # Frame de seleção
        selection_frame = ttk.LabelFrame(main_frame, text="Selecao de Arquivos", padding=10)
        selection_frame.pack(fill="both", expand=True)
        
        # Botões de controle
        control_frame = ttk.Frame(selection_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(control_frame, text="Atualizar Lista", 
                  command=self.refresh_file_list).pack(side="left")
        ttk.Button(control_frame, text="Selecionar Todos", 
                  command=self.select_all).pack(side="left", padx=(5, 0))
        ttk.Button(control_frame, text="Limpar Selecao", 
                  command=self.clear_selection).pack(side="left", padx=(5, 0))
        
        # Frame com listas
        lists_frame = ttk.Frame(selection_frame)
        lists_frame.pack(fill="both", expand=True)
        
        # Lista de arquivos disponíveis
        available_frame = ttk.LabelFrame(lists_frame, text="Arquivos Disponiveis", padding=5)
        available_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Listbox com scrollbar
        self.available_listbox = tk.Listbox(available_frame, selectmode="extended")
        available_scrollbar = ttk.Scrollbar(available_frame, orient="vertical", 
                                           command=self.available_listbox.yview)
        self.available_listbox.configure(yscrollcommand=available_scrollbar.set)
        
        self.available_listbox.pack(side="left", fill="both", expand=True)
        available_scrollbar.pack(side="right", fill="y")
        
        # Botões de transferência
        transfer_frame = ttk.Frame(lists_frame)
        transfer_frame.pack(side="left", padx=10)
        
        ttk.Button(transfer_frame, text=">>", 
                  command=self.add_selected).pack(pady=2)
        ttk.Button(transfer_frame, text="<<", 
                  command=self.remove_selected).pack(pady=2)
        
        # Lista de arquivos selecionados
        selected_frame = ttk.LabelFrame(lists_frame, text="Arquivos Selecionados", padding=5)
        selected_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.selected_listbox = tk.Listbox(selected_frame, selectmode="extended")
        selected_scrollbar = ttk.Scrollbar(selected_frame, orient="vertical", 
                                          command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_listbox.pack(side="left", fill="both", expand=True)
        selected_scrollbar.pack(side="right", fill="y")
        
        # Status
        self.status_label = ttk.Label(selection_frame, text="Pronto")
        self.status_label.pack(pady=(10, 0))
        
        # Botões principais
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.compile_button = ttk.Button(button_frame, text="Compilar CSV", 
                                        command=self.start_compilation,
                                        style="Accent.TButton")
        self.compile_button.pack(side="left", padx=10)
        
        ttk.Button(button_frame, text="Fechar", 
                  command=self.root.quit).pack(side="left", padx=10)
    
    def select_directory(self):
        """Seleciona diretório dos cromatogramas."""
        directory = filedialog.askdirectory(
            title="Selecione a pasta dos cromatogramas",
            initialdir=self.chromatograms_dir
        )
        if directory:
            self.chromatograms_dir = directory
            self.dir_var.set(directory)
            self.refresh_file_list()
    
    def select_output_file(self):
        """Seleciona arquivo de saída."""
        filename = filedialog.asksaveasfilename(
            title="Salvar CSV combinado como",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=self.output_file
        )
        if filename:
            self.output_file = filename
            self.output_var.set(filename)
    
    def refresh_file_list(self):
        """Atualiza a lista de arquivos disponíveis."""
        self.available_files = []
        
        if os.path.exists(self.chromatograms_dir):
            for file in os.listdir(self.chromatograms_dir):
                if file.endswith('.csv'):
                    self.available_files.append(file)
        
        self.available_files.sort()
        
        # Atualiza a listbox
        self.available_listbox.delete(0, tk.END)
        for file in self.available_files:
            # Remove a extensão .csv para exibição
            display_name = file[:-4] if file.endswith('.csv') else file
            self.available_listbox.insert(tk.END, display_name)
        
        self.update_status()
    
    def add_selected(self):
        """Adiciona arquivos selecionados à lista de compilação."""
        selection = self.available_listbox.curselection()
        for index in reversed(selection):  # Reversed para manter índices válidos
            file = self.available_files[index]
            if file not in self.selected_files:
                self.selected_files.append(file)
                display_name = file[:-4] if file.endswith('.csv') else file
                self.selected_listbox.insert(tk.END, display_name)
        
        self.update_status()
    
    def remove_selected(self):
        """Remove arquivos da lista de compilação."""
        selection = self.selected_listbox.curselection()
        for index in reversed(selection):
            if index < len(self.selected_files):
                del self.selected_files[index]
                self.selected_listbox.delete(index)
        
        self.update_status()
    
    def select_all(self):
        """Seleciona todos os arquivos disponíveis."""
        self.selected_files = self.available_files.copy()
        
        self.selected_listbox.delete(0, tk.END)
        for file in self.selected_files:
            display_name = file[:-4] if file.endswith('.csv') else file
            self.selected_listbox.insert(tk.END, display_name)
        
        self.update_status()
    
    def clear_selection(self):
        """Limpa a seleção."""
        self.selected_files = []
        self.selected_listbox.delete(0, tk.END)
        self.update_status()
    
    def update_status(self):
        """Atualiza o status."""
        available_count = len(self.available_files)
        selected_count = len(self.selected_files)
        self.status_label.config(text=f"{available_count} disponiveis | {selected_count} selecionados")
    
    def compile_chromatograms(self):
        """Compila os cromatogramas selecionados."""
        try:
            if not self.selected_files:
                messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
                return
            
            self.status_label.config(text="Carregando dados...")
            self.root.update_idletasks()
            
            # Carrega o primeiro arquivo para estabelecer o eixo de tempo
            first_file_path = os.path.join(self.chromatograms_dir, self.selected_files[0])
            first_df = pd.read_csv(first_file_path)
            
            if 'tempo_min' not in first_df.columns:
                messagebox.showerror("Erro", f"Arquivo {self.selected_files[0]} não contém coluna 'tempo_min'")
                return
            
            # Prepara os dados
            data_dict = {'tempo_min': first_df['tempo_min'].values}
            common_time_axis = first_df['tempo_min'].values
            
            # Processa cada arquivo selecionado
            for i, filename in enumerate(self.selected_files):
                self.status_label.config(text=f"Processando {i+1}/{len(self.selected_files)}: {filename}")
                self.root.update_idletasks()
                
                file_path = os.path.join(self.chromatograms_dir, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    
                    if 'intensidade' not in df.columns:
                        print(f"Aviso: {filename} não contém coluna 'intensidade' - pulando...")
                        continue
                    
                    sample_name = filename[:-4]  # Remove .csv extension
                    intensidade = df['intensidade'].values
                    
                    # Verifica compatibilidade de tamanho
                    if len(intensidade) == len(common_time_axis):
                        data_dict[sample_name] = intensidade
                    elif len(intensidade) > len(common_time_axis):
                        print(f"Aviso: {sample_name} truncado ({len(intensidade)} -> {len(common_time_axis)})")
                        data_dict[sample_name] = intensidade[:len(common_time_axis)]
                    else:
                        print(f"Aviso: {sample_name} preenchido com NaN ({len(intensidade)} -> {len(common_time_axis)})")
                        padded_intensidade = np.full(len(common_time_axis), np.nan)
                        padded_intensidade[:len(intensidade)] = intensidade
                        data_dict[sample_name] = padded_intensidade
                        
                except Exception as e:
                    print(f"Erro ao processar {filename}: {e}")
                    continue
            
            self.status_label.config(text="Salvando arquivo combinado...")
            self.root.update_idletasks()
            
            # Cria DataFrame final
            combined_df = pd.DataFrame(data_dict)
            
            # Salva arquivo
            combined_df.to_csv(self.output_file, index=False)
            
            # Sucesso
            samples_count = len(combined_df.columns) - 1  # -1 for tempo_min column
            points_count = len(combined_df)
            
            messagebox.showinfo("Sucesso", 
                               f"Arquivo compilado com sucesso!\n\n"
                               f"Arquivo: {self.output_file}\n"
                               f"Amostras: {samples_count}\n"
                               f"Pontos: {points_count}")
            
            self.status_label.config(text=f"Compilacao concluida: {samples_count} amostras, {points_count} pontos")
            
        except Exception as e:
            error_msg = f"Erro durante a compilacao: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            self.status_label.config(text="Erro na compilacao")
            print(error_msg)
        finally:
            self.compile_button.config(state="normal")
    
    def start_compilation(self):
        """Inicia a compilação em thread separada."""
        if not self.selected_files:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo!")
            return
        
        # Confirmar compilação
        confirm_msg = (f"Compilar {len(self.selected_files)} arquivo(s) em:\n\n"
                      f"{self.output_file}\n\n"
                      f"Continuar?")
        
        if not messagebox.askyesno("Confirmar Compilacao", confirm_msg):
            return
        
        # Desabilitar botão e iniciar thread
        self.compile_button.config(state="disabled")
        
        compile_thread = threading.Thread(target=self.compile_chromatograms)
        compile_thread.daemon = True
        compile_thread.start()

def main():
    root = tk.Tk()
    app = ChromatogramCompilerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()