import pandas as pd

import matplotlib.pyplot as plt

import scipy.signal

import seaborn as sns

from hplc.quant import Chromatogram

from hplc.io import load_chromatogram


sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})

df = load_chromatogram('cromatogramas/DCS_E5110.csv', cols=['time', 'signal'])

signal_norm = (df['signal'] - df['signal'].min()) / (df['signal'].max() - df['signal'].min())
peak_locations, _ = scipy.signal.find_peaks(signal_norm, height=0.2, distance=10, prominence=0.01)


chrom=Chromatogram(df)

peaks=chrom.fit_peaks(rel_height=0.90, prominence=0.06)

chrom.show()
plt.show()