# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-09-30

### Added
- Initial release of Chroma HPLC data analysis package
- HPLCDataImporter class for importing data from CSV, TXT, and Excel files
- ChromatogramAnalyzer class for chromatogram analysis
- Peak detection functionality using scipy.signal.find_peaks
- Data smoothing using Savitzky-Golay filter
- Baseline calculation (linear and polynomial methods)
- Peak integration using trapezoidal rule
- Statistical analysis functions
- Comprehensive documentation in README.md
- Example scripts demonstrating usage
- Setup.py for package installation
- Requirements.txt with dependencies
- .gitignore for Python projects

### Features
- Import HPLC data from multiple file formats
- Detect and identify peaks in chromatograms
- Calculate peak areas and retention times
- Perform baseline correction
- Smooth noisy chromatogram data
- Generate statistical summaries
- Export results as pandas DataFrames

[0.1.0]: https://github.com/LadabioMPAR/Chroma/releases/tag/v0.1.0
