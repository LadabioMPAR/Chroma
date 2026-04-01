import argparse
import os
import sys

# Ensure we can import chroma_lib
# Adds the parent directory of 'scripts' (which is 'src_refactor') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chroma_lib.io import load_chromatogram
from chroma_lib.processing import detect_peaks
from chroma_lib.fitting import fit_peak_gamma
from chroma_lib.models import gamma_peak
from chroma_lib.plotting import plot_chromatogram_fit, plot_residuals
import numpy as np
import pandas as pd
from tqdm import tqdm

# CONFIGURATION - PEAK DETECTION
PEAK_PROMINENCE = 0.1
PEAK_DISTANCE = 1
PEAK_HEIGHT = None
PEAK_WIDTH = None
PEAK_THRESHOLD = None
EXTRA_WINDOW = 10

def main():
    parser = argparse.ArgumentParser(description="Batch process chromatograms.")
    parser.add_argument("directory", help="Directory containing CSV files to process.")
    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        sys.exit(1)

    # Output setup
    input_dir_name = os.path.basename(args.directory.rstrip("/\\"))
    plots_dir = os.path.join("plots", input_dir_name)
    plots_res_dir = os.path.join(plots_dir, "residuos")
    results_dir = "resultados"
    
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(plots_res_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Get all CSV files
    files = sorted([f for f in os.listdir(args.directory) if f.lower().endswith('.csv')])
    
    if not files:
        print(f"No CSV files found in {args.directory}")
        return

    print(f"Found {len(files)} files in '{args.directory}'. Starting processing...")
    
    all_results = []
    
    for filename in tqdm(files, desc="Processando", unit="arquivo"):
        filepath = os.path.join(args.directory, filename)
        
        try:
            # 1. Load
            time, signal = load_chromatogram(filepath)
            
            # 2. Detect
            peaks = detect_peaks(
                time, 
                signal, 
                prominence=PEAK_PROMINENCE, 
                distance=PEAK_DISTANCE,
                height=PEAK_HEIGHT,
                width=PEAK_WIDTH,
                threshold=PEAK_THRESHOLD
            )
            
            if len(peaks) == 0:
                continue
                
            # 3. Fit
            fit_total = np.zeros_like(signal)
            fit_peaks_list = []
            areas = []
            
            for i, peak_idx in enumerate(peaks):
                res = fit_peak_gamma(time, signal, peak_idx, extra_window=EXTRA_WINDOW)
                
                if res['success']:
                    params = res['params']
                    # Generate full curve for this peak
                    fit_curve = gamma_peak(time, *params)
                    
                    fit_total += fit_curve
                    fit_peaks_list.append(fit_curve)
                    
                    # Calculate Area
                    area = np.trapezoid(fit_curve, time)
                    areas.append(area)
                    
                    # Store Result
                    all_results.append({
                        "arquivo": filename,
                        "tempo_pico": round(time[peak_idx], 1),
                        "amplitude": params[0],
                        "k": params[2],
                        "theta": params[3],
                        "area": area,
                        "R2": res['R2']
                    })
                else:
                    # Failed fit
                    all_results.append({
                        "arquivo": filename,
                        "tempo_pico": round(time[peak_idx], 1),
                        "amplitude": np.nan,
                        "k": np.nan,
                        "theta": np.nan,
                        "area": np.nan,
                        "R2": np.nan
                    })
                    # Add zero contribution so index matching for plotting doesn't break?
                    # Actually if fit fails, we probably shouldn't plot it as a fit.
                    # But to keep list lengths sync with peaks indices:
                    fit_peaks_list.append(np.zeros_like(time))
                    areas.append(0)

            # 4. Plot
            plot_chromatogram_fit(
                time, signal, peaks, fit_peaks_list, fit_total, 
                areas, filename, plots_dir
            )
            plot_residuals(
                time, signal, fit_peaks_list, fit_total, peaks, 
                filename, plots_res_dir
            )
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()

    # 5. Save Summary
    csv_name = f"parametros_ajuste_gamma_{input_dir_name}.csv"
    csv_path = os.path.join(results_dir, csv_name)
    df = pd.DataFrame(all_results)
    df.to_csv(csv_path, index=False)
    
    print("\n Análise concluída!")
    print(f"Resultados salvos em: {csv_path}")
    print(f"Gráficos salvos em: {plots_dir}")

if __name__ == "__main__":
    main()
