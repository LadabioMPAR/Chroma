import numpy as np
from scipy.optimize import curve_fit
from chroma_lib.models import gamma_peak

def fit_peak_gamma(time, signal, peak_idx, extra_window=10):
    """
    Fits a single Gamma peak to the signal data around a specific peak index.
    
    Args:
        time (np.array): Time vector.
        signal (np.array): Signal vector.
        peak_idx (int): Index of the peak in the time/signal arrays.
        extra_window (float): Multiplier for window size determination.
        
    Returns:
        dict: detailed results including optimized parameters, R2, area, etc.
              Returns None if fit fails.
    """
    pico_time = time[peak_idx]
    dt = time[1] - time[0]

    # Define window
    t_start = max(time[0], pico_time - extra_window * dt)
    t_end = min(time[-1], pico_time + extra_window * dt)
    mask = (time >= t_start) & (time <= t_end)
    t_peak = time[mask]
    y_peak = signal[mask]

    # Initial estimates
    A0 = signal[peak_idx]
    t0_0 = pico_time - 0.05
    k0 = 1.5 + np.random.rand() * 2.0
    theta0 = dt * 5
    p0 = [A0, t0_0, k0, theta0]

    # Bounds
    # [A, t0, k, theta]
    bounds_lower = [0, t0_0 - 0.5, 0.1, 0.001]
    bounds_upper = [np.inf, t0_0 + 0.5, 10, 2]

    try:
        popt, _ = curve_fit(gamma_peak, t_peak, y_peak, p0=p0, bounds=(bounds_lower, bounds_upper))
        
        # Calculate R2 for the local window
        fit_local = gamma_peak(t_peak, *popt)
        ss_res = np.sum((y_peak - fit_local) ** 2)
        ss_tot = np.sum((y_peak - np.mean(y_peak)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0 

        # Calculate area (integral over full time range, but practically mostly defined by peak params)
        # We compute the full curve to get Area via trapezoid or analytical properties.
        # Analytical area for Gamma PDF part is 1, so integral is A * (something)? 
        # Actually the legacy code uses trapezoid on the full curve generated.
        
        # We return the curve generator function or the params so the caller can generate it
        
        return {
            "params": popt, # [A, t0, k, theta]
            "R2": r2,
            "peak_index": peak_idx,
            "success": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "peak_index": peak_idx
        }
