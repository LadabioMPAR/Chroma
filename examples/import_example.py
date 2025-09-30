"""
Example demonstrating data import from different file formats.

This example shows how to:
1. Import data from CSV files
2. Import data from TXT files
3. Import data from Excel files
"""

from chroma import HPLCDataImporter
import pandas as pd
import numpy as np
from pathlib import Path


def create_sample_files():
    """Create sample data files for demonstration."""
    # Create sample data
    time = np.linspace(0, 10, 100)
    signal = 50 + 20 * np.sin(time) + np.random.normal(0, 2, 100)
    
    data = pd.DataFrame({
        'Time': time,
        'Signal': signal
    })
    
    # Create examples directory if it doesn't exist
    examples_dir = Path(__file__).parent
    
    # Save as CSV
    csv_path = examples_dir / 'sample_data.csv'
    data.to_csv(csv_path, index=False)
    print(f"Created sample CSV file: {csv_path}")
    
    # Save as TXT (tab-delimited)
    txt_path = examples_dir / 'sample_data.txt'
    data.to_csv(txt_path, sep='\t', index=False)
    print(f"Created sample TXT file: {txt_path}")
    
    # Save as Excel
    excel_path = examples_dir / 'sample_data.xlsx'
    data.to_excel(excel_path, index=False)
    print(f"Created sample Excel file: {excel_path}")
    
    return csv_path, txt_path, excel_path


def main():
    """Main example function."""
    print("Chroma - Data Import Example")
    print("=" * 50)
    
    # Create sample files
    print("\n1. Creating sample data files...")
    csv_path, txt_path, excel_path = create_sample_files()
    
    # Initialize importer
    importer = HPLCDataImporter()
    
    # Import CSV
    print("\n2. Importing CSV file...")
    csv_data = importer.load_csv(csv_path)
    print(f"   Loaded {len(csv_data)} rows")
    print(f"   Columns: {list(csv_data.columns)}")
    print("\n   Preview:")
    print(importer.preview(3))
    
    # Import TXT
    print("\n3. Importing TXT file...")
    txt_data = importer.load_txt(txt_path)
    print(f"   Loaded {len(txt_data)} rows")
    print(f"   Columns: {list(txt_data.columns)}")
    
    # Import Excel
    print("\n4. Importing Excel file...")
    excel_data = importer.load_excel(excel_path)
    print(f"   Loaded {len(excel_data)} rows")
    print(f"   Columns: {list(excel_data.columns)}")
    
    # Show metadata
    print("\n5. File metadata:")
    metadata = importer.get_metadata()
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 50)
    print("Import example complete!")
    print("\nNote: Sample files have been created in the examples directory.")
    print("You can delete them if no longer needed.")


if __name__ == "__main__":
    main()
