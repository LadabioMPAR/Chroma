"""
Data Import Module for HPLC Data

This module provides tools to import and parse HPLC data from various file formats.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Dict, List, Optional


class HPLCDataImporter:
    """
    A class for importing HPLC data from various file formats.
    
    Supports common HPLC export formats including CSV, TXT, and Excel files.
    """
    
    def __init__(self):
        """Initialize the HPLC Data Importer."""
        self.data = None
        self.metadata = {}
    
    def load_csv(self, filepath: Union[str, Path], 
                 time_column: str = 'Time',
                 signal_column: str = 'Signal',
                 delimiter: str = ',',
                 skiprows: int = 0) -> pd.DataFrame:
        """
        Load HPLC data from a CSV file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to the CSV file
        time_column : str, optional
            Name of the time/retention time column (default: 'Time')
        signal_column : str, optional
            Name of the signal/absorbance column (default: 'Signal')
        delimiter : str, optional
            Column delimiter (default: ',')
        skiprows : int, optional
            Number of rows to skip at the beginning (default: 0)
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing the HPLC data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            self.data = pd.read_csv(filepath, delimiter=delimiter, skiprows=skiprows)
            self.metadata['filepath'] = str(filepath)
            self.metadata['format'] = 'CSV'
            
            # Try to identify time and signal columns if they exist
            if time_column not in self.data.columns and len(self.data.columns) >= 2:
                # Assume first column is time, second is signal
                self.data.columns = [time_column, signal_column] + list(self.data.columns[2:])
            
            return self.data
        
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    
    def load_txt(self, filepath: Union[str, Path],
                 delimiter: str = '\t',
                 skiprows: int = 0) -> pd.DataFrame:
        """
        Load HPLC data from a TXT file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to the TXT file
        delimiter : str, optional
            Column delimiter (default: tab)
        skiprows : int, optional
            Number of rows to skip at the beginning (default: 0)
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing the HPLC data
        """
        return self.load_csv(filepath, delimiter=delimiter, skiprows=skiprows)
    
    def load_excel(self, filepath: Union[str, Path],
                   sheet_name: Union[str, int] = 0) -> pd.DataFrame:
        """
        Load HPLC data from an Excel file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to the Excel file
        sheet_name : str or int, optional
            Sheet name or index (default: 0 - first sheet)
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing the HPLC data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            self.data = pd.read_excel(filepath, sheet_name=sheet_name)
            self.metadata['filepath'] = str(filepath)
            self.metadata['format'] = 'Excel'
            self.metadata['sheet_name'] = sheet_name
            
            return self.data
        
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """
        Get the loaded HPLC data.
        
        Returns
        -------
        pd.DataFrame or None
            The loaded data, or None if no data has been loaded
        """
        return self.data
    
    def get_metadata(self) -> Dict:
        """
        Get metadata about the loaded data.
        
        Returns
        -------
        dict
            Metadata dictionary
        """
        return self.metadata
    
    def preview(self, n: int = 5) -> Optional[pd.DataFrame]:
        """
        Preview the first n rows of loaded data.
        
        Parameters
        ----------
        n : int, optional
            Number of rows to display (default: 5)
        
        Returns
        -------
        pd.DataFrame or None
            First n rows of data, or None if no data loaded
        """
        if self.data is not None:
            return self.data.head(n)
        return None
