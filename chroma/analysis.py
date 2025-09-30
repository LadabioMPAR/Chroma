"""
Chromatogram Analysis Module

This module provides tools for analyzing HPLC chromatogram data, including
peak detection, integration, and visualization.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from scipy import signal


class ChromatogramAnalyzer:
    """
    A class for analyzing HPLC chromatogram data.
    
    Provides methods for baseline correction, peak detection, peak integration,
    and other common chromatogram analysis tasks.
    """
    
    def __init__(self, data: pd.DataFrame = None,
                 time_column: str = 'Time',
                 signal_column: str = 'Signal'):
        """
        Initialize the Chromatogram Analyzer.
        
        Parameters
        ----------
        data : pd.DataFrame, optional
            HPLC chromatogram data
        time_column : str, optional
            Name of the time/retention time column (default: 'Time')
        signal_column : str, optional
            Name of the signal/absorbance column (default: 'Signal')
        """
        self.data = data
        self.time_column = time_column
        self.signal_column = signal_column
        self.peaks = None
        self.baseline = None
    
    def set_data(self, data: pd.DataFrame,
                 time_column: str = 'Time',
                 signal_column: str = 'Signal'):
        """
        Set the chromatogram data.
        
        Parameters
        ----------
        data : pd.DataFrame
            HPLC chromatogram data
        time_column : str, optional
            Name of the time column
        signal_column : str, optional
            Name of the signal column
        """
        self.data = data
        self.time_column = time_column
        self.signal_column = signal_column
    
    def smooth_data(self, window_size: int = 5, poly_order: int = 2) -> np.ndarray:
        """
        Smooth chromatogram data using Savitzky-Golay filter.
        
        Parameters
        ----------
        window_size : int, optional
            Size of the smoothing window (must be odd, default: 5)
        poly_order : int, optional
            Order of polynomial for smoothing (default: 2)
        
        Returns
        -------
        np.ndarray
            Smoothed signal data
        """
        if self.data is None:
            raise ValueError("No data loaded. Use set_data() first.")
        
        if window_size % 2 == 0:
            window_size += 1  # Ensure odd window size
        
        signal_data = self.data[self.signal_column].values
        smoothed = signal.savgol_filter(signal_data, window_size, poly_order)
        
        return smoothed
    
    def find_peaks(self, height: Optional[float] = None,
                   threshold: Optional[float] = None,
                   distance: Optional[int] = None,
                   prominence: Optional[float] = None,
                   width: Optional[float] = None) -> Tuple[np.ndarray, Dict]:
        """
        Find peaks in the chromatogram.
        
        Parameters
        ----------
        height : float, optional
            Minimum peak height
        threshold : float, optional
            Minimum threshold for peak detection
        distance : int, optional
            Minimum distance between peaks (in data points)
        prominence : float, optional
            Minimum prominence of peaks
        width : float, optional
            Minimum width of peaks (in data points)
        
        Returns
        -------
        tuple
            (peak_indices, peak_properties)
        """
        if self.data is None:
            raise ValueError("No data loaded. Use set_data() first.")
        
        signal_data = self.data[self.signal_column].values
        
        peaks, properties = signal.find_peaks(
            signal_data,
            height=height,
            threshold=threshold,
            distance=distance,
            prominence=prominence,
            width=width
        )
        
        self.peaks = peaks
        
        # Add retention times to properties
        if len(peaks) > 0:
            properties['retention_times'] = self.data[self.time_column].iloc[peaks].values
        
        return peaks, properties
    
    def calculate_baseline(self, method: str = 'linear') -> np.ndarray:
        """
        Calculate baseline for the chromatogram.
        
        Parameters
        ----------
        method : str, optional
            Method for baseline calculation ('linear' or 'polynomial')
        
        Returns
        -------
        np.ndarray
            Baseline values
        """
        if self.data is None:
            raise ValueError("No data loaded. Use set_data() first.")
        
        signal_data = self.data[self.signal_column].values
        
        if method == 'linear':
            # Simple linear baseline from first to last point
            x = np.arange(len(signal_data))
            baseline = np.linspace(signal_data[0], signal_data[-1], len(signal_data))
        elif method == 'polynomial':
            # Polynomial baseline fitting
            x = np.arange(len(signal_data))
            # Fit a low-order polynomial to approximate baseline
            coeffs = np.polyfit(x, signal_data, 3)
            baseline = np.polyval(coeffs, x)
        else:
            raise ValueError(f"Unknown baseline method: {method}")
        
        self.baseline = baseline
        return baseline
    
    def integrate_peak(self, start_idx: int, end_idx: int,
                      baseline_corrected: bool = True) -> float:
        """
        Integrate a peak area.
        
        Parameters
        ----------
        start_idx : int
            Starting index of the peak
        end_idx : int
            Ending index of the peak
        baseline_corrected : bool, optional
            Whether to subtract baseline (default: True)
        
        Returns
        -------
        float
            Integrated peak area
        """
        if self.data is None:
            raise ValueError("No data loaded. Use set_data() first.")
        
        time_data = self.data[self.time_column].iloc[start_idx:end_idx+1].values
        signal_data = self.data[self.signal_column].iloc[start_idx:end_idx+1].values
        
        if baseline_corrected:
            if self.baseline is None:
                self.calculate_baseline()
            baseline_segment = self.baseline[start_idx:end_idx+1]
            signal_data = signal_data - baseline_segment
        
        # Use numpy's trapezoid function (trapz is deprecated in newer scipy)
        area = np.trapz(signal_data, time_data)
        return area
    
    def get_peak_summary(self) -> Optional[pd.DataFrame]:
        """
        Get a summary of detected peaks.
        
        Returns
        -------
        pd.DataFrame or None
            Summary of peaks with retention times and areas
        """
        if self.peaks is None or len(self.peaks) == 0:
            return None
        
        summary_data = []
        for i, peak_idx in enumerate(self.peaks):
            retention_time = self.data[self.time_column].iloc[peak_idx]
            height = self.data[self.signal_column].iloc[peak_idx]
            
            summary_data.append({
                'Peak': i + 1,
                'Retention Time': retention_time,
                'Height': height,
                'Index': peak_idx
            })
        
        return pd.DataFrame(summary_data)
    
    def calculate_statistics(self) -> Dict:
        """
        Calculate basic statistics for the chromatogram.
        
        Returns
        -------
        dict
            Dictionary containing statistics (mean, std, min, max, etc.)
        """
        if self.data is None:
            raise ValueError("No data loaded. Use set_data() first.")
        
        signal_data = self.data[self.signal_column]
        
        stats = {
            'mean': signal_data.mean(),
            'std': signal_data.std(),
            'min': signal_data.min(),
            'max': signal_data.max(),
            'median': signal_data.median(),
            'range': signal_data.max() - signal_data.min()
        }
        
        return stats
