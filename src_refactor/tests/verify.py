import sys
import os
import numpy as np
import unittest.mock as mock

# ---------------------------------------------------------
# Setup Paths
# ---------------------------------------------------------
# Path to legacy code (root of the workspace)
legacy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
# Path to new refactored code (src_refactor directory)
new_lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

sys.path.append(legacy_path)
sys.path.append(new_lib_path)

# ---------------------------------------------------------
# Mocking Legacy Execution
# ---------------------------------------------------------
# analise_gamma.py runs code at the top level including GUI calls.
# We must mock these to import the function safely.

mock_tk = mock.MagicMock()
# Prevent UI blocking
mock_tk.Tk.return_value.withdraw = mock.MagicMock()
# Prevent SystemExit/Crash by returning a valid dummy path if it's called
mock_tk.filedialog.askdirectory.return_value = "/tmp/dummy_test_path"

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.filedialog'] = mock_tk.filedialog

# PATCH MATPLOTLIB before import to avoid AttributeError in mock.patch or GUI backend issues
mock_plt = mock.MagicMock()
sys.modules['matplotlib.pyplot'] = mock_plt
sys.modules['matplotlib'] = mock.MagicMock()
sys.modules['matplotlib'].pyplot = mock_plt

print("Verifying gamma_peak implementation...")

# Context manager to suppress side effects like file globbing or dir creation
# We patch glob and makedirs because the script runs them at top level
with mock.patch('glob.glob', return_value=[]), \
     mock.patch('os.makedirs'), \
     mock.patch('pandas.read_csv'):
    
    try:
        import analise_gamma # Legacy import
    except ImportError:
        # Fallback if the legacy file is not strictly "analise_gamma.py" or path issue
        # Based on file listing, it is "analise_gamma.py" in root.
        print("Error importing legacy analise_gamma.py. Check path.")
        sys.exit(1)

from chroma_lib.models import gamma_peak # New import

# ---------------------------------------------------------
# Verification Logic
# ---------------------------------------------------------
def test_gamma_equivalence():
    # 1. Define random inputs
    # Using linspace for t to simulate actual use case
    t = np.linspace(0, 50, 500)
    
    # Random parameters typical for this domain
    A = np.random.uniform(10, 100)
    t0 = np.random.uniform(5, 10)
    k = np.random.uniform(1.5, 3.5)
    theta = np.random.uniform(2, 5)

    print(f"Testing with params: A={A:.2f}, t0={t0:.2f}, k={k:.2f}, theta={theta:.2f}")

    # 2. Compute results
    res_legacy = analise_gamma.gamma_peak(t, A, t0, k, theta)
    res_new = gamma_peak(t, A, t0, k, theta)

    # 3. Assert equality
    try:
        assert np.allclose(res_legacy, res_new, rtol=1e-10, atol=1e-10)
        print("SUCCESS: Both implementations return identical results.")
    except AssertionError:
        diff = np.max(np.abs(res_legacy - res_new))
        print(f"FAILURE: Implementations differ. Max diff: {diff}")
        sys.exit(1)

if __name__ == "__main__":
    test_gamma_equivalence()
