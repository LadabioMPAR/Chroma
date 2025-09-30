"""
Basic example of using Chroma to import and analyze HPLC data.

This example demonstrates:
1. Importing data from a CSV file
2. Basic peak detection
3. Calculating statistics
"""

from chroma import HPLCDataImporter, ChromatogramAnalyzer
import numpy as np
import pandas as pd


def create_sample_data():
    """Create sample HPLC data for demonstration."""
    # Generate sample chromatogram data with synthetic peaks
    time = np.linspace(0, 20, 1000)  # 20 minutes, 1000 data points
    
    # Create baseline with slight drift
    baseline = 10 + 0.5 * time
    
    # Add several Gaussian peaks
    def gaussian(x, mu, sigma, amplitude):
        return amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
    
    signal = baseline.copy()
    # Peak 1: retention time 5.0 min
    signal += gaussian(time, 5.0, 0.2, 100)
    # Peak 2: retention time 8.5 min
    signal += gaussian(time, 8.5, 0.3, 150)
    # Peak 3: retention time 12.0 min
    signal += gaussian(time, 12.0, 0.25, 80)
    # Peak 4: retention time 15.5 min
    signal += gaussian(time, 15.5, 0.35, 120)
    
    # Add some noise
    noise = np.random.normal(0, 2, len(time))
    signal += noise
    
    # Create DataFrame
    data = pd.DataFrame({
        'Time': time,
        'Signal': signal
    })
    
    return data


def main():
    """Main example function."""
    print("Chroma - HPLC Data Analysis Example")
    print("=" * 50)
    
    # Create sample data
    print("\n1. Creating sample HPLC data...")
    data = create_sample_data()
    print(f"   Generated {len(data)} data points")
    print(f"   Time range: {data['Time'].min():.2f} - {data['Time'].max():.2f} minutes")
    
    # Initialize analyzer
    print("\n2. Initializing ChromatogramAnalyzer...")
    analyzer = ChromatogramAnalyzer(data, time_column='Time', signal_column='Signal')
    
    # Calculate statistics
    print("\n3. Calculating chromatogram statistics...")
    stats = analyzer.calculate_statistics()
    print(f"   Mean signal: {stats['mean']:.2f}")
    print(f"   Signal range: {stats['min']:.2f} - {stats['max']:.2f}")
    print(f"   Standard deviation: {stats['std']:.2f}")
    
    # Smooth the data
    print("\n4. Smoothing data...")
    smoothed = analyzer.smooth_data(window_size=11, poly_order=3)
    print(f"   Smoothed {len(smoothed)} data points")
    
    # Find peaks
    print("\n5. Detecting peaks...")
    peaks, properties = analyzer.find_peaks(
        height=50,      # Minimum peak height
        distance=50,    # Minimum distance between peaks
        prominence=30   # Minimum prominence
    )
    print(f"   Found {len(peaks)} peaks")
    
    # Get peak summary
    print("\n6. Peak Summary:")
    peak_summary = analyzer.get_peak_summary()
    if peak_summary is not None:
        print(peak_summary.to_string(index=False))
        
        # Calculate peak areas
        print("\n7. Calculating peak areas...")
        analyzer.calculate_baseline(method='linear')
        
        for i, peak_idx in enumerate(peaks):
            # Define integration window (±50 points around peak)
            start_idx = max(0, peak_idx - 50)
            end_idx = min(len(data) - 1, peak_idx + 50)
            
            area = analyzer.integrate_peak(start_idx, end_idx, baseline_corrected=True)
            print(f"   Peak {i+1}: Area = {area:.2f}")
    
    print("\n" + "=" * 50)
    print("Analysis complete!")


if __name__ == "__main__":
    main()
