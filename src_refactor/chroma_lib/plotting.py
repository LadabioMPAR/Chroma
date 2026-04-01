import matplotlib.pyplot as plt
import numpy as np
import os

def plot_chromatogram_fit(time, signal, peaks_indices, fit_peaks_list, fit_total, areas, filename, output_dir):
    """
    Plots the original signal, the individual peak fits, and the total fit.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    colors = plt.cm.tab20(np.linspace(0, 1, len(peaks_indices)))
    
    plt.figure(figsize=(12, 6))
    plt.plot(time, signal, color='black', lw=1.5, label="Cromatograma")
    
    for i, fit_peak in enumerate(fit_peaks_list):
        p_idx = peaks_indices[i]
        p_time = time[p_idx]
        plt.fill_between(time, 0, fit_peak, color=colors[i], alpha=0.5,
                         label=f"Pico {round(p_time, 1)}, Área ≈ {areas[i]:.2f}")
        
    plt.plot(time, fit_total, 'r--', lw=2, label="Soma de ajustes Gamma")
    # Plot detected peaks markers
    if len(peaks_indices) > 0:
        plt.scatter(time[peaks_indices], signal[peaks_indices], color='black', s=50, label="Picos detectados")
        
    plt.xlabel("Tempo")
    plt.ylabel("Sinal")
    plt.title(f"Cromatograma ajustado (Gamma) — {filename}")
    plt.legend(loc='upper right', fontsize=8, ncol=2)
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_ajuste_gamma.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_residuals(time, signal, fit_peaks_list, fit_total, peaks_indices, filename, output_dir):
    """
    Plots the residuals of the fit.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    colors = plt.cm.tab20(np.linspace(0, 1, len(peaks_indices)))
    residuals = signal - fit_total
    
    plt.figure(figsize=(12, 4))
    plt.axhline(0, color='black', lw=1, linestyle='--', label="Zero")
    
    for i, fit_peak in enumerate(fit_peaks_list):
        p_idx = peaks_indices[i]
        p_time = time[p_idx]
        plt.plot(time, fit_peak, color=colors[i], alpha=0.7, lw=1,
                 label=f"Pico {round(p_time, 1)}")
                 
    plt.plot(time, residuals, color='blue', lw=1.5, label="Resíduo total")
    plt.xlabel("Tempo")
    plt.ylabel("Resíduo")
    plt.title(f"Resíduos do ajuste Gamma — {filename}")
    plt.legend(loc='upper right', fontsize=8, ncol=2)
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_residuos.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
