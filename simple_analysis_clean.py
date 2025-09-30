import pandas as pd
import matplotlib.pyplot as plt
import scipy
import seaborn as sns
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

df = pd.read_csv("cromatogramas/DCS_E521.csv")
# print(df)
"""plt.plot(df['tempo_min'], df['intensidade'], 'r-')
plt.xlabel('time [min]')
plt.ylabel('signal intensity [mV]')
plt.xlim([0, 30])
 plt.show()"""

# acessar colunas
tempo = df["tempo_min"]
intensidade = df["intensidade"]

# Create a normalized signal
signal_norm = (df['intensidade'] - df['intensidade'].min()) / (df['intensidade'].max() - df['intensidade'].min())

# Find peaks with a low prominence filter of 0.01
peak_locations, _ = scipy.signal.find_peaks(signal_norm, prominence=0.01)

# Plot the  original trace and overlay vertical lines with location of peaks
plt.plot(df['tempo_min'], signal_norm, 'k-', label='normalized chromatogram')
plt.vlines(df['tempo_min'].values[peak_locations], 0, 1, linestyle='--',
           color='dodgerblue', label='peak location')
plt.xlabel('time [min]')
plt.ylabel('normalized signal intensity')
plt.xlim([0, 30])
plt.title('prominence filter = 0.01')
plt.legend()
plt.show()
