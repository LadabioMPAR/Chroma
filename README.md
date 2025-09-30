# Chroma

A Python package for importing, processing, and analyzing HPLC (High-Performance Liquid Chromatography) chromatogram data.

## Features

- **Data Import**: Import HPLC data from various file formats (CSV, TXT, Excel)
- **Chromatogram Analysis**: 
  - Peak detection and identification
  - Baseline correction
  - Peak integration
  - Data smoothing
  - Statistical analysis

## Installation

1. Clone this repository:
```bash
git clone https://github.com/LadabioMPAR/Chroma.git
cd Chroma
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Importing HPLC Data

```python
from chroma import HPLCDataImporter

# Create an importer instance
importer = HPLCDataImporter()

# Load data from CSV file
data = importer.load_csv('path/to/your/data.csv', 
                         time_column='Time', 
                         signal_column='Signal')

# Preview the data
print(importer.preview())

# Load from Excel file
data = importer.load_excel('path/to/your/data.xlsx', sheet_name=0)
```

### Analyzing Chromatograms

```python
from chroma import ChromatogramAnalyzer

# Create an analyzer instance
analyzer = ChromatogramAnalyzer(data, time_column='Time', signal_column='Signal')

# Smooth the data
smoothed_signal = analyzer.smooth_data(window_size=5, poly_order=2)

# Find peaks
peaks, properties = analyzer.find_peaks(height=100, distance=10, prominence=50)

# Get peak summary
peak_summary = analyzer.get_peak_summary()
print(peak_summary)

# Calculate baseline
baseline = analyzer.calculate_baseline(method='linear')

# Integrate a peak
peak_area = analyzer.integrate_peak(start_idx=100, end_idx=200, baseline_corrected=True)

# Get chromatogram statistics
stats = analyzer.calculate_statistics()
print(stats)
```

### Complete Example

```python
from chroma import HPLCDataImporter, ChromatogramAnalyzer

# Import data
importer = HPLCDataImporter()
data = importer.load_csv('hplc_data.csv')

# Analyze
analyzer = ChromatogramAnalyzer(data)
peaks, properties = analyzer.find_peaks(prominence=50)

# Display results
print(f"Found {len(peaks)} peaks")
print(analyzer.get_peak_summary())
```

## File Format Requirements

### CSV/TXT Files
- Should contain at least two columns: one for time/retention time and one for signal/absorbance
- Default column names are 'Time' and 'Signal' (can be customized)
- Common delimiters supported (comma, tab, semicolon, etc.)

### Excel Files
- Data should be in a single sheet (can specify which sheet)
- Similar column structure as CSV files

## Dependencies

- numpy >= 1.20.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- openpyxl >= 3.0.0 (for Excel support)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.
