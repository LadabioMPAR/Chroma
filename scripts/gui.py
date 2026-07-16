"""GUI: assistente de calibração e quantificação.

Encadeia, numa janela só:
    1. Ler CDF            -> converte .cdf em cromatogramas CSV
    2. Padrões e analitos -> marca quais CSVs são padrões e define os analitos
                             (nome + tempo do pico)
    3. Curvas             -> informa a concentração de cada analito em cada
                             padrão e calcula as retas (conc = a·área + b)
    4. Amostras           -> calcula as concentrações de uma pasta e salva o CSV

É apenas uma camada de conveniência sobre a biblioteca chroma/. As ferramentas
de scripts/ continuam independentes e podem ser usadas isoladamente.

Uso:
    python scripts/gui.py
"""

import os
import sys
import glob
import queue
import threading
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd

from chroma import config, io, peaks, fitting, calibration, plotting
from chroma.models import available_models


def _scrollable(parent):
    """Devolve um frame interno com scroll vertical/horizontal."""
    canvas = tk.Canvas(parent, highlightthickness=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    return inner


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chroma — Calibração e Quantificação")
        self.geometry("980x760")

        self.cfg = config.load_config()
        self.log_q = queue.Queue()
        self.analitos = []        # [{"name":..., "peak_time":...}]
        self.padroes = []         # caminhos dos CSVs marcados como padrão
        self.grid_entries = {}    # (caminho_padrao, nome_analito) -> Entry
        self.curves = []          # curvas calculadas
        self.df_conc = None       # DataFrame de concentrações
        self._buttons = []

        self._build()
        self.after(100, self._drain)

    # ---------------- infraestrutura ----------------
    def log(self, msg):
        self.log_q.put(("log", msg, None))

    def _append(self, msg):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _busy(self, on):
        for b in self._buttons:
            b.configure(state="disabled" if on else "normal")
        self.configure(cursor="watch" if on else "")

    def _run_async(self, work, done=None):
        self._busy(True)
        def worker():
            try:
                res = work()
                self.log_q.put(("done", res, done))
            except Exception:
                self.log_q.put(("error", traceback.format_exc(), None))
        threading.Thread(target=worker, daemon=True).start()

    def _drain(self):
        try:
            while True:
                kind, payload, cb = self.log_q.get_nowait()
                if kind == "log":
                    self._append(payload)
                elif kind == "done":
                    self._busy(False)
                    if cb:
                        cb(payload)
                elif kind == "error":
                    self._busy(False)
                    self._append("ERRO:\n" + payload)
                    messagebox.showerror("Erro", payload.strip().split("\n")[-1])
        except queue.Empty:
            pass
        self.after(100, self._drain)

    def _btn(self, parent, text, cmd, **kw):
        b = ttk.Button(parent, text=text, command=cmd, **kw)
        self._buttons.append(b)
        return b

    # ---------------- construção da UI ----------------
    def _build(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        self._tab_ler()
        self._tab_padroes()
        self._tab_curvas()
        self._tab_amostras()

        frm = ttk.LabelFrame(self, text="Log")
        frm.pack(fill="both", expand=False, padx=8, pady=(0, 8))
        self.txt_log = tk.Text(frm, height=9, state="disabled", wrap="word")
        sb = ttk.Scrollbar(frm, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        self.txt_log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _path_row(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=var, width=70).grid(row=row, column=1, sticky="we", padx=6)
        self._btn(parent, "Procurar...",
                  lambda: var.set(filedialog.askdirectory(initialdir=var.get()) or var.get())
                  ).grid(row=row, column=2)
        parent.columnconfigure(1, weight=1)

    # ---- aba 1
    def _tab_ler(self):
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="1. Ler CDF")

        self.var_raw = tk.StringVar(value=config.resolve(self.cfg["paths"]["raw_cdf"]))
        self.var_out = tk.StringVar(value=config.resolve(self.cfg["paths"]["chromatograms"]))
        self.var_png = tk.BooleanVar(value=True)

        self._path_row(f, "Pasta com os .cdf:", self.var_raw, 0)
        self._path_row(f, "Salvar CSVs em:", self.var_out, 1)
        ttk.Checkbutton(f, text="Gerar também um PNG por cromatograma",
                        variable=self.var_png).grid(row=2, column=1, sticky="w", pady=4)
        self._btn(f, "Ler CDF", self._do_ler).grid(row=3, column=1, sticky="w", pady=10)
        ttk.Label(f, foreground="#666",
                  text="Já tem os cromatogramas em CSV? Pule direto para a aba 2."
                  ).grid(row=4, column=1, sticky="w")

    # ---- aba 2
    def _tab_padroes(self):
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="2. Padrões e analitos")

        self.var_chrom = tk.StringVar(value=config.resolve(self.cfg["paths"]["chromatograms"]))
        top = ttk.Frame(f); top.pack(fill="x")
        self._path_row(top, "Pasta dos cromatogramas:", self.var_chrom, 0)
        self._btn(top, "Atualizar lista", self._refresh_files).grid(row=0, column=3, padx=6)

        body = ttk.Frame(f); body.pack(fill="both", expand=True, pady=8)

        left = ttk.LabelFrame(body, text="Marque os arquivos que são PADRÕES (Ctrl/Shift p/ vários)")
        left.pack(side="left", fill="both", expand=True)
        self.lb_files = tk.Listbox(left, selectmode=tk.EXTENDED)
        sb = ttk.Scrollbar(left, command=self.lb_files.yview)
        self.lb_files.configure(yscrollcommand=sb.set)
        self.lb_files.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        right = ttk.LabelFrame(body, text="Analitos de interesse")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        add = ttk.Frame(right); add.pack(fill="x", pady=4)
        ttk.Label(add, text="Nome:").grid(row=0, column=0)
        self.var_an_nome = tk.StringVar()
        ttk.Entry(add, textvariable=self.var_an_nome, width=14).grid(row=0, column=1, padx=4)
        ttk.Label(add, text="Tempo do pico (min):").grid(row=0, column=2)
        self.var_an_t = tk.StringVar()
        ttk.Entry(add, textvariable=self.var_an_t, width=8).grid(row=0, column=3, padx=4)
        self._btn(add, "Adicionar", self._add_analito).grid(row=0, column=4, padx=4)

        self.tv_an = ttk.Treeview(right, columns=("nome", "t"), show="headings", height=8)
        self.tv_an.heading("nome", text="Analito")
        self.tv_an.heading("t", text="Tempo do pico")
        self.tv_an.pack(fill="both", expand=True, pady=4)
        self._btn(right, "Remover selecionado", self._del_analito).pack(anchor="w", pady=4)

        self._btn(f, "Montar grade de concentrações →", self._build_grid).pack(anchor="e")
        self._refresh_files()

    # ---- aba 3
    def _tab_curvas(self):
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="3. Curvas")

        opt = ttk.LabelFrame(f, text="Opções do ajuste"); opt.pack(fill="x")
        self.var_fit_b = tk.BooleanVar(value=bool(self.cfg["calibration"].get("fit_intercept", False)))
        self.var_model = tk.StringVar(value=self.cfg["individual_fit"].get("model", "gamma"))
        self.var_prom = tk.StringVar(value=str(self.cfg["individual_fit"]["peaks"].get("prominence", 0.1)))
        self.var_tol = tk.StringVar(value=str(self.cfg["calibration"].get("peak_tolerance", 0.5)))

        ttk.Checkbutton(opt, text="Estimar intercepto b (senão, b = 0)",
                        variable=self.var_fit_b).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(opt, text="Modelo:").grid(row=0, column=1, padx=(16, 2))
        ttk.Combobox(opt, textvariable=self.var_model, values=available_models(),
                     width=10, state="readonly").grid(row=0, column=2)
        ttk.Label(opt, text="Prominence:").grid(row=0, column=3, padx=(16, 2))
        ttk.Entry(opt, textvariable=self.var_prom, width=7).grid(row=0, column=4)
        ttk.Label(opt, text="Tolerância do pico:").grid(row=0, column=5, padx=(16, 2))
        ttk.Entry(opt, textvariable=self.var_tol, width=7).grid(row=0, column=6)

        gf = ttk.LabelFrame(f, text="Concentração de cada analito em cada padrão")
        gf.pack(fill="both", expand=True, pady=8)
        self.grid_host = _scrollable(gf)

        self._btn(f, "Calcular curvas", self._calc_curvas).pack(anchor="w")

        self.tv_curvas = ttk.Treeview(f, columns=("an", "a", "b", "r2", "n"),
                                      show="headings", height=6)
        for c, t in [("an", "Analito"), ("a", "a"), ("b", "b"), ("r2", "R²"), ("n", "n pontos")]:
            self.tv_curvas.heading(c, text=t)
        self.tv_curvas.pack(fill="x", pady=8)

    # ---- aba 4
    def _tab_amostras(self):
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="4. Amostras → concentrações")

        self.var_samples = tk.StringVar(value=config.resolve(self.cfg["quantify"]["input_dir"]))
        top = ttk.Frame(f); top.pack(fill="x")
        self._path_row(top, "Pasta das amostras:", self.var_samples, 0)

        bar = ttk.Frame(f); bar.pack(fill="x", pady=8)
        self._btn(bar, "Calcular concentrações", self._calc_conc).pack(side="left")
        self._btn(bar, "Salvar CSV como...", self._save_conc).pack(side="left", padx=8)

        self.tv_conc = ttk.Treeview(f, show="headings", height=14)
        sb = ttk.Scrollbar(f, command=self.tv_conc.yview)
        self.tv_conc.configure(yscrollcommand=sb.set)
        self.tv_conc.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ---------------- ações ----------------
    def _do_ler(self):
        raw, out = self.var_raw.get(), self.var_out.get()
        png = self.var_png.get()
        if not os.path.isdir(raw):
            messagebox.showerror("Erro", f"Pasta não encontrada:\n{raw}")
            return

        def work():
            self.log(f"Lendo .cdf de {raw} ...")
            return io.convert_cdf_folder(
                raw, out,
                plots_dir=config.resolve(self.cfg["paths"]["plots"]) if png else None,
                summary_csv=config.resolve(self.cfg["paths"]["summary_csv"]),
                on_progress=lambda i, t, n: self.log(f"  [{i}/{t}] {n}"),
            )

        def done(criados):
            self.log(f"OK — {len(criados)} cromatograma(s) em {out}")
            self.var_chrom.set(out)
            self._refresh_files()
            self.nb.select(1)

        self._run_async(work, done)

    def _refresh_files(self):
        d = self.var_chrom.get()
        self.lb_files.delete(0, "end")
        for p in sorted(glob.glob(os.path.join(d, "*.csv"))):
            self.lb_files.insert("end", os.path.basename(p))

    def _add_analito(self):
        nome = self.var_an_nome.get().strip()
        try:
            t = float(self.var_an_t.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Tempo do pico deve ser um número (min).")
            return
        if not nome:
            messagebox.showerror("Erro", "Informe o nome do analito.")
            return
        if any(a["name"] == nome for a in self.analitos):
            messagebox.showerror("Erro", f"Analito '{nome}' já foi adicionado.")
            return
        self.analitos.append({"name": nome, "peak_time": t})
        self.tv_an.insert("", "end", values=(nome, t))
        self.var_an_nome.set("")
        self.var_an_t.set("")

    def _del_analito(self):
        for item in self.tv_an.selection():
            nome = self.tv_an.item(item, "values")[0]
            self.analitos = [a for a in self.analitos if a["name"] != nome]
            self.tv_an.delete(item)

    def _build_grid(self):
        sel = [self.lb_files.get(i) for i in self.lb_files.curselection()]
        if not sel:
            messagebox.showerror("Erro", "Marque ao menos um arquivo como padrão (aba 2).")
            return
        if not self.analitos:
            messagebox.showerror("Erro", "Adicione ao menos um analito (aba 2).")
            return

        d = self.var_chrom.get()
        self.padroes = [os.path.join(d, f) for f in sel]

        for w in self.grid_host.winfo_children():
            w.destroy()
        self.grid_entries.clear()

        ttk.Label(self.grid_host, text="Padrão", font=("", 9, "bold")).grid(row=0, column=0, padx=6, pady=4, sticky="w")
        for j, an in enumerate(self.analitos, start=1):
            ttk.Label(self.grid_host, text=f"{an['name']}\n(t≈{an['peak_time']})",
                      font=("", 9, "bold")).grid(row=0, column=j, padx=6, pady=4)

        for i, p in enumerate(self.padroes, start=1):
            ttk.Label(self.grid_host, text=os.path.basename(p)).grid(row=i, column=0, padx=6, sticky="w")
            for j, an in enumerate(self.analitos, start=1):
                e = ttk.Entry(self.grid_host, width=10)
                e.grid(row=i, column=j, padx=6, pady=2)
                self.grid_entries[(p, an["name"])] = e

        self.log(f"Grade montada: {len(self.padroes)} padrão(ões) × {len(self.analitos)} analito(s). "
                 "Preencha as concentrações (deixe vazio para ignorar o ponto).")
        self.nb.select(2)

    def _read_opts(self):
        return {
            "model": self.var_model.get(),
            "prominence": float(self.var_prom.get().replace(",", ".")),
            "tol": float(self.var_tol.get().replace(",", ".")),
            "fit_b": self.var_fit_b.get(),
            "extra_window": self.cfg["individual_fit"].get("extra_window", 10),
            "distance": self.cfg["individual_fit"]["peaks"].get("distance", 1),
        }

    def _fit_file(self, path, o):
        """Ajusta um cromatograma e devolve os peak_results."""
        t, y = io.load_chromatogram(path)
        pk = {"method": "prominence", "prominence": o["prominence"], "distance": o["distance"]}
        idxs = peaks.detect(y, pk)
        return fitting.fit_peaks_individual(
            t, y, idxs, model_name=o["model"], extra_window=o["extra_window"]
        )

    def _calc_curvas(self):
        if not self.grid_entries:
            messagebox.showerror("Erro", "Monte a grade de concentrações primeiro (aba 2).")
            return
        try:
            o = self._read_opts()
        except ValueError:
            messagebox.showerror("Erro", "Prominence e tolerância devem ser números.")
            return

        # Lê os campos na thread principal (widgets não são thread-safe)
        concs = {k: e.get().strip() for k, e in self.grid_entries.items()}
        analitos = list(self.analitos)
        padroes = list(self.padroes)

        def work():
            cache = {}
            for p in padroes:
                cache[p] = self._fit_file(p, o)
                self.log(f"  ajustado: {os.path.basename(p)} ({len(cache[p])} pico(s))")

            registros = []
            for an in analitos:
                xs, ys = [], []
                for p in padroes:
                    txt = concs.get((p, an["name"]), "")
                    if not txt:
                        continue
                    try:
                        conc = float(txt.replace(",", "."))
                    except ValueError:
                        self.log(f"  [{an['name']}] '{txt}' não é número em {os.path.basename(p)}; ignorado")
                        continue
                    area = calibration.area_at(cache[p], an["peak_time"], o["tol"])
                    if area is None:
                        self.log(f"  [{an['name']}] sem pico perto de t={an['peak_time']} "
                                 f"em {os.path.basename(p)}; ponto ignorado")
                        continue
                    xs.append(area); ys.append(conc)

                if len(xs) < 2:
                    self.log(f"  [{an['name']}] pontos insuficientes ({len(xs)}); analito ignorado")
                    continue

                a, b, r2, n = calibration.fit_linear(xs, ys, fit_intercept=o["fit_b"])
                registros.append({
                    "analito": an["name"], "tempo_pico": an["peak_time"],
                    "a_slope": a, "b_intercept": b, "R2": r2, "n_pontos": n,
                })
                pdir = config.ensure_dir(os.path.join(self.cfg["paths"]["plots"], "calibracao"))
                plotting.plot_calibration(xs, ys, a, b, r2, an["name"],
                                          os.path.join(pdir, f"calibracao_{an['name']}.png"))
                self.log(f"  [{an['name']}] conc = {a:.5g}·área + {b:.5g}   R²={r2:.4f}  (n={n})")

            if registros:
                txt_path = config.resolve(self.cfg["calibration"]["output_txt"])
                os.makedirs(os.path.dirname(txt_path), exist_ok=True)
                calibration.save_txt(txt_path, registros)
                self.log(f"Curvas salvas em {txt_path}")
            return registros

        def done(registros):
            self.curves = [{"analito": r["analito"], "tempo_pico": r["tempo_pico"],
                            "a": r["a_slope"], "b": r["b_intercept"]} for r in registros]
            self.tv_curvas.delete(*self.tv_curvas.get_children())
            for r in registros:
                self.tv_curvas.insert("", "end", values=(
                    r["analito"], f"{r['a_slope']:.6g}", f"{r['b_intercept']:.6g}",
                    f"{r['R2']:.4f}", r["n_pontos"]))
            if registros:
                self.nb.select(3)

        self._run_async(work, done)

    def _calc_conc(self):
        if not self.curves:
            messagebox.showerror("Erro", "Calcule as curvas primeiro (aba 3).")
            return
        d = self.var_samples.get()
        if not os.path.isdir(d):
            messagebox.showerror("Erro", f"Pasta não encontrada:\n{d}")
            return
        try:
            o = self._read_opts()
        except ValueError:
            messagebox.showerror("Erro", "Prominence e tolerância devem ser números.")
            return
        curves = list(self.curves)

        def work():
            files = sorted(glob.glob(os.path.join(d, "*.csv")))
            self.log(f"Calculando concentrações de {len(files)} amostra(s)...")
            linhas = []
            for f in files:
                prs = self._fit_file(f, o)
                linha = {"arquivo": os.path.basename(f)}
                for c in curves:
                    area = calibration.area_at(prs, c["tempo_pico"], o["tol"])
                    linha[c["analito"]] = (calibration.apply_curve(area, c["a"], c["b"])
                                           if area is not None else np.nan)
                linhas.append(linha)
            df = pd.DataFrame(linhas)
            out = config.resolve(self.cfg["quantify"]["output_csv"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            df.to_csv(out, index=False)
            self.log(f"Concentrações salvas em {out}")
            return df

        def done(df):
            self.df_conc = df
            cols = list(df.columns)
            self.tv_conc.configure(columns=cols)
            for c in cols:
                self.tv_conc.heading(c, text=c)
                self.tv_conc.column(c, width=120, anchor="center")
            self.tv_conc.delete(*self.tv_conc.get_children())
            for _, row in df.iterrows():
                vals = [row["arquivo"]] + [
                    "—" if pd.isna(row[c]) else f"{row[c]:.4f}" for c in cols[1:]
                ]
                self.tv_conc.insert("", "end", values=vals)

        self._run_async(work, done)

    def _save_conc(self):
        if self.df_conc is None:
            messagebox.showerror("Erro", "Calcule as concentrações primeiro.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         filetypes=[("CSV", "*.csv")],
                                         initialfile="concentracoes.csv")
        if p:
            self.df_conc.to_csv(p, index=False)
            self.log(f"Salvo: {p}")


if __name__ == "__main__":
    App().mainloop()
