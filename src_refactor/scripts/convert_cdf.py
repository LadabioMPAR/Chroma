import os
import argparse
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chroma_lib.io import load_cdf_metadata_and_signal

def unique_name(path):
    """
    If the file exists, append _1, _2...
    Duplicates logic from ler.py.
    """
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path

    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1

    return new_path

def main():
    parser = argparse.ArgumentParser(description="Convert CDF files to CSV and generate plots + summary.")
    parser.add_argument("input_folder", help="Folder containing .cdf files.")
    parser.add_argument("--out-csv", default="cromatogramas", help="Output folder for CSVs.")
    parser.add_argument("--out-plots", default="plots", help="Output folder for Plots.")
    parser.add_argument("--summary", default="resumo.csv", help="Path to summary CSV.")
    args = parser.parse_args()

    if not os.path.exists(args.input_folder):
        print(f"Error: Input folder {args.input_folder} does not exist.")
        sys.exit(1)

    os.makedirs(args.out_csv, exist_ok=True)
    os.makedirs(args.out_plots, exist_ok=True)

    cdf_files = [f for f in os.listdir(args.input_folder) if f.lower().endswith(".cdf")]
    
    if not cdf_files:
        print(f"No .cdf files found in {args.input_folder}")
        sys.exit(0)

    print(f"Found {len(cdf_files)} CDF files. Processing...")
    
    summary_data = []

    for fname in cdf_files:
        filepath = os.path.join(args.input_folder, fname)
        
        try:
            # 1. Read CDF using refactored function
            result = load_cdf_metadata_and_signal(filepath)
            meta = result["metadata"]
            intensidade = result["signal"]
            dt = result["dt"]
            delay = result["delay"]
            
            # 2. Time calc
            tempo_s = np.arange(len(intensidade)) * dt + delay
            tempo_min = tempo_s / 60.0
            
            sample_name = meta.get("sample_name", os.path.splitext(fname)[0]).strip()
            
            # 3. Save CSV
            out_csv_path = os.path.join(args.out_csv, f"{sample_name}.csv")
            out_csv_path = unique_name(out_csv_path)
            
            df = pd.DataFrame({"time": tempo_min, "signal": intensidade})
            df.to_csv(out_csv_path, index=False)
            
            # 4. Plot
            out_png_path = os.path.join(args.out_plots, f"{sample_name}.png")
            out_png_path = unique_name(out_png_path)
            
            plt.figure(figsize=(10, 5))
            plt.plot(tempo_min, intensidade, color="blue")
            plt.title(f"Cromatograma - {sample_name}")
            plt.xlabel("Tempo (min)")
            plt.ylabel("Intensidade (mV)")
            plt.savefig(out_png_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            # 5. Collect Summary Info
            linha = {
                "arquivo": fname,
                "sample_name": sample_name,
                "injection_date_time_stamp": meta.get("injection_date_time_stamp", ""),
                "sample_id_comments": meta.get("sample_id_comments", ""),
                "sample_type": meta.get("sample_type", ""),
                "sample_injection_volume": meta.get("sample_injection_volume", ""),
                "sample_amount": meta.get("sample_amount", ""),
                "detector_name": meta.get("detector_name", ""),
                "detector_unit": meta.get("detector_unit", ""),
                "retention_unit": meta.get("retention_unit", ""),
                "n_pontos": len(intensidade),
                "tempo_final_min": float(tempo_min[-1]) if len(tempo_min) > 0 else 0
            }
            summary_data.append(linha)
            
            print(f"Converted: {fname} -> {os.path.basename(out_csv_path)}")

        except Exception as e:
            print(f"Error processing {fname}: {e}")

    # 6. Write Summary
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        # Using to_csv directly handles headers properly
        df_summary.to_csv(args.summary, index=False)
        print(f"\nSummary saved to: {args.summary}")
    
    print("Done!")

if __name__ == "__main__":
    main()
