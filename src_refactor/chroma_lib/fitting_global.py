import numpy as np
from scipy.optimize import least_squares
from chroma_lib.processing import detect_peaks
from chroma_lib.models import gamma_peak

def residuals(params, all_t, all_y, n_picos_list):
    """
    Global residual function where k and theta are shared across all chromatograms.
    params structure: [k, theta, A1_1, mu1_1, A1_2, mu1_2, ..., A2_1, mu2_1, ...]
    """
    k, theta = params[0], params[1]
    idx = 2
    res = []

    for t, y_exp, n_picos in zip(all_t, all_y, n_picos_list):
        y_pred = np.zeros_like(t)
        for _ in range(n_picos):
            A = params[idx]
            mu = params[idx + 1]
            y_pred += gamma_peak(t, A, mu, k, theta)
            idx += 2

        res.append(y_pred - y_exp)

    return np.concatenate(res)

def perform_global_fit(all_t, all_y, **kwargs):
    """
    Performs global fitting on multiple chromatograms constraining k and theta to be uniform.
    
    Args:
        all_t (list of np.array): List of time arrays.
        all_y (list of np.array): List of signal arrays.
        **kwargs: Peak detection parameters passed to detect_peaks (e.g., prominence, distance, height, threshold).
        
    Returns:
        dict: containing 'result' (least_squares output), 'n_picos_list', and 'initial_params'.
    """
    
    k0 = 5.0
    theta0 = 0.2
    params0 = [k0, theta0]
    
    n_picos_list = []
    
    # Pre-detect peaks to set up parameters
    for t, y in zip(all_t, all_y):
        peaks = detect_peaks(t, y, **kwargs)

        if len(peaks) == 0:
            peaks = [np.argmax(y)]

        n_picos_list.append(len(peaks))

        for pk in peaks:
            A0 = y[pk]
            mu0 = t[pk]
            params0 += [A0, mu0]
            
    # Perform Optimization
    result = least_squares(
        residuals,
        params0,
        args=(all_t, all_y, n_picos_list),
        bounds=(0, np.inf),
        verbose=1
    )
    
    return {
        "optimization_result": result,
        "n_picos_list": n_picos_list,
        "k_global": result.x[0],
        "theta_global": result.x[1]
    }
