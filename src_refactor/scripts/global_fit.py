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
from chroma_lib.models import gamma_peak
from chroma_lib.fitting_global import perform_global_fit

# CONFIGURATION - PEAK DETECTION (Passed to detect_peaks)
# Note: In global fit, be mindful that excessive peaks can greatly increase computation time
PEAK_PROMINENCE = 0.1
PEAK_DISTANCE = 5
PEAK_HEIGHT = None
PEAK_WIDTH = None
PEAK_THRESHOLD = None

def generate_reports(fit_data, files, all_t, all_y, output_dir):
    """
    Generates plots and CSV reports from the global fit results.
    """
    result = fit_data["optimization_result"]
    n_picos_list = fit_data["n_picos_list"]
    
    os.makedirs(output_dir, exist_ok=True)
    
    params = result.x
    k_global, theta_global = params[0], params[1]

    idx = 2
    registros = []

    for file_path, t, y_exp, n_picos in zip(files, all_t, all_y, n_picos_list):

        nome = os.path.splitext(os.path.basename(file_path))[0]

        y_sum = np.zeros_like(t)
        picos_individuais = []

        for j in range(n_picos):
            A = params[idx]
            mu = params[idx + 1]
            y_pico = gamma_peak(t, A, mu, k_global, theta_global)

            y_sum += y_pico
            picos_individuais.append((A, mu, y_pico))

            registros.append({
                "arquivo": nome,
                "pico_id": j + 1,
                "A": A,
                "mu": mu,
                "k_global": k_global,
                "theta_global": theta_global
            })

            idx += 2

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(t, y_exp, 'k-', label="Experimental")
        for j, (A, mu, y_pico) in enumerate(picos_individuais):
            plt.plot(t, y_pico, '--', label=f"Pico {j+1}")
        plt.plot(t, y_sum, 'r-', linewidth=2, label="Soma dos picos")

        plt.title(f"Ajuste Global (k={k_global:.2f}, theta={theta_global:.2f}) — {nome}")
        plt.xlabel("Tempo")
        plt.ylabel("Sinal")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()

        plt.savefig(os.path.join(output_dir, f"{nome}_global_fit.png"), dpi=300)
        plt.close()

    # Relatório CSV
    df = pd.DataFrame(registros)
    csv_path = os.path.join(output_dir, "relatorio_picos_global.csv")
    df.to_csv(csv_path, index=False)

    print(f"\nPlots salvos em: {output_dir}")
    print(f"Relatório salvo em: {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Perform global fitting (locked k, theta) on a set of chromatograms.")
    parser.add_argument("path_pattern", help="Glob pattern for CSV files (e.g. 'cromatogramas/teste/*.csv')")
    parser.add_argument("--out", default="resultados_global", help="Output directory")
    args = parser.parse_args()

    # Expand glob
    files = sorted(glob.glob(args.path_pattern))
    if not files:
        print(f"No files found matching: {args.path_pattern}")
        sys.exit(1)

    print(f"Loading {len(files)} files...")
    
    all_t = []
    all_y = []
    
    for f in files:
        t, y = load_chromatogram(f)
        all_t.append(t)
        all_y.append(y)
        
    print("Starting global fit (locking k and theta)...")
    
    fit_data = perform_global_fit(
        all_t, 
        all_y, 
        prominence=PEAK_PROMINENCE,
        distance=PEAK_DISTANCE,
        height=PEAK_HEIGHT,
        width=PEAK_WIDTH,
        threshold=PEAK_THRESHOLD
    )
    
    print(f"Optimization Success: {fit_data['optimization_result'].success}")
    print(f"Estimated locked parameters: k={fit_data['k_global']:.4f}, theta={fit_data['theta_global']:.4f}")
    
    generate_reports(fit_data, files, all_t, all_y, args.out)

if __name__ == "__main__":
    main()
