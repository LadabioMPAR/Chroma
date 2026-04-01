import argparse
import sys
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chroma_lib.io import load_chromatogram
from chroma_lib.processing import linear_baseline_correction, beads_baseline

def process_file_linear(filepath, output_dir):
    try:
        # Load
        t, y = load_chromatogram(filepath)
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]

        # Correction
        y_corr, baseline = linear_baseline_correction(t, y)
        
        # Save
        df_out = pd.DataFrame({'time': t, 'signal': y_corr}) # Standard output format matching input
        # Note: Original script overwrites "signal" column.
        out_path = os.path.join(output_dir, f"{base_name}_corrigido.csv")
        df_out.to_csv(out_path, index=False)
        
        # Plot
        fig, axes = plt.subplots(2, 1, figsize=(10,8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        
        axes[0].plot(t, y, label="Sinal original", alpha=0.8)
        axes[0].plot(t, baseline, 'r--', label="Linha de base (ajuste linear)", linewidth=2)
        axes[0].set_ylabel("Sinal")
        axes[0].legend()
        axes[0].set_title(f"Ajuste linear da linha de base - {base_name}")

        axes[1].plot(t, y_corr, label="Sinal corrigido", color='green')
        axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
        axes[1].set_xlabel("Tempo")
        axes[1].set_ylabel("Sinal corrigido")
        axes[1].legend()

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"{base_name}_corrigido.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        
        print(f"[Linear] Processed {filename}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def process_file_beads(filepath, output_dir, lam=1e6, fc=0.015, r=0.05, nit=80):
    try:
        # Load
        t, y = load_chromatogram(filepath)
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]

        # Correction
        # Using parameters from legacy script default calls inside the loop
        baseline = beads_baseline(y, lam=lam, fc=fc, r=r, nit=nit)
        y_corr = y - baseline
        
        # Save
        # Legacy script saves time, signal, baseline, corrected
        out = pd.DataFrame({"time": t, "signal": y, "baseline": baseline, "corrected": y_corr})
        out_path = os.path.join(output_dir, f"{base_name}_BEADS.csv")
        out.to_csv(out_path, index=False)
        
        # Plot
        plt.figure(figsize=(12,6))
        plt.plot(t, y, label="Original", alpha=0.6)
        plt.plot(t, baseline, label="Baseline (BEADS)", linewidth=2)
        plt.plot(t, y_corr, label="Corrigido", linewidth=1)
        plt.legend()
        plt.title(f"Correção de linha de base (BEADS) - {base_name}")
        
        plot_path = os.path.join(output_dir, f"{base_name}_BEADS.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        
        print(f"[BEADS] Processed {filename}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Baseline correction utility.")
    parser.add_argument("path_pattern", help="Glob pattern for CSV files (e.g. 'cromatogramas/*.csv')")
    parser.add_argument("--method", choices=['linear', 'beads'], required=True, help="Correction method.")
    parser.add_argument("--out", default="corrected_output", help="Output directory.")
    
    # BEADS params
    parser.add_argument("--lam", type=float, default=1e6, help="BEADS lambda")
    parser.add_argument("--fc", type=float, default=0.015, help="BEADS fc")
    parser.add_argument("--r", type=float, default=0.05, help="BEADS r")
    parser.add_argument("--nit", type=int, default=80, help="BEADS iterations")

    args = parser.parse_args()

    files = sorted(glob.glob(args.path_pattern))
    if not files:
        print(f"No files found matching {args.path_pattern}")
        sys.exit(1)
        
    os.makedirs(args.out, exist_ok=True)
    
    print(f"Processing {len(files)} files with method {args.method}...")
    
    for f in files:
        if args.method == 'linear':
            process_file_linear(f, args.out)
        elif args.method == 'beads':
            process_file_beads(f, args.out, lam=args.lam, fc=args.fc, r=args.r, nit=args.nit)

if __name__ == "__main__":
    main()
