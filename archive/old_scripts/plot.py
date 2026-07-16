import pandas as pd
import matplotlib.pyplot as plt

# Ler o arquivo CSV
df = pd.read_csv("cromatogramas/EXP 6/DCS_E5105.csv")

# Plotar o cromatograma
plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["signal"], color="black", label="Cromatograma")

# Linha vertical para glicose
plt.axvline(x=9.6, color="red", linestyle="--", linewidth=1, label="Glicose ")
plt.axvline(x=7.95, color="green", linestyle="--", linewidth=1, label="Celobiose ")
plt.axvline(x=10.25, color="purple", linestyle="--", linewidth=1, label="Xilose ")


# Rótulos e título
plt.xlabel("Time (min)")
plt.ylabel("Signal (a.u.)")
plt.title("Cromatograma - E4105")
plt.legend()
plt.tight_layout()
plt.savefig("DCS_E5105_cromatograma.png", dpi=150)
plt.show()

