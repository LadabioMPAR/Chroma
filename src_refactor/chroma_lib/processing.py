from scipy.signal import find_peaks, savgol_filter
from scipy import sparse
import numpy as np

def detect_peaks(time, signal, **kwargs):
    """
    detect_peaks wrapper around scipy.signal.find_peaks.
    Returns indices of peaks.
    """
    if len(time) != len(signal):
        raise ValueError("Time and signal arrays must have same length")
        
    # Default values compatible with previous defaults
    kwargs.setdefault('prominence', 0.1)
    kwargs.setdefault('distance', 1)

    peaks, _ = find_peaks(signal, **kwargs)
    return peaks

def beads_baseline(y, lam=3e5, fc=0.01, r=0.5, nit=60):
    """
    Baseline Estimation And Denoising with Sparsity (BEADS).
    
    Ported from correct_baseline_beads.py.
    """
    N = len(y)
    
    # Original implementation uses dense matrices which is memory heavy.
    # Refactoring slightly to use sparse matrices for efficiency while maintaining logic.
    # Original logic: D = np.diff(np.eye(N), 2, axis=0) -> (N-2)xN second derivative matrix
    
    # Sparse construction:
    D = sparse.diags([1, -2, 1], [0, 1, 2], shape=(N-2, N), format='csc')
    
    # H = lam * (D.T @ D)
    H = lam * (D.T @ D)
    
    win = int(max(5, int(fc * N)))
    if win % 2 == 0:
        win += 1
    
    z = y.copy()
    w = np.ones(N)

    for _ in range(nit):
        W = sparse.diags(w, format='csc')
        # Solve (W + H)z = Wy
        # Using sparse solver
        mat = W + H
        rhs = w * y
        z = sparse.linalg.spsolve(mat, rhs)
        
        # Apply smoothing
        z = savgol_filter(z, win, 3)
        
        # Update weights (asymmetry)
        d = y - z
        w = 1 / (1 + (d / r) ** 2)

    return z

def linear_baseline_correction(time, signal):
    """
    Fits a linear polynomial to the signal (baseline) and subtracts it.
    Ported from correct_base_linear.py.
    
    Returns: corrected_signal, baseline
    """
    coef = np.polyfit(time, signal, 1)
    baseline = np.polyval(coef, time)
    corrected_signal = signal - baseline
    return corrected_signal, baseline

