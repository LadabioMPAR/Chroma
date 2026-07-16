import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Construindo os conjuntos de dados a partir das tabelas
exp1_data = {
    'Tempo': [0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    'Celobiose_Media': [1.385, 1.586, 1.540, 1.585, 1.651, 1.596, 1.509, 1.508, 1.534, 1.519, 1.503, 1.531, 1.509, 1.494],
    'Celobiose_Erro': [0.030, 0.081, 0.081, 0.056, 0.022, 0.040, 0.006, 0.038, 0.025, 0.008, 0.025, 0.032, 0.021, 0.017],
    'Glicose_Media': [7.758, 7.735, 8.354, 9.095, 9.840, 9.989, 9.846, 10.432, 10.641, 10.905, 11.069, 11.168, 11.443, 11.448],
    'Glicose_Erro': [0.141, 0.441, 0.533, 0.471, 0.334, 0.119, 0.108, 0.508, 0.380, 0.422, 0.185, 0.110, 0.093, 0.147],
    'Xilose_Media': [3.682, 4.477, 4.756, 5.157, 5.517, 5.604, 5.531, 5.766, 5.822, 5.938, 6.002, 6.046, 6.176, 6.163],
    'Xilose_Erro': [0.021, 0.012, 0.027, 0.037, 0.029, 0.011, 0.004, 0.002, 0.007, 0.006, 0.014, 0.043, 0.027, 0.009],
    'Experimento': ['Batelada 1'] * 14
}

exp2_data = {
    'Tempo': [0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24],
    'Celobiose_Media': [1.066, 1.220, 1.258, 1.228, 1.330, 1.322, 1.392, 1.408, 1.342, 1.421, 1.324, 1.366, 1.211, 1.104, 1.062, 1.154, 1.112],
    'Celobiose_Erro': [np.nan, 0.010, 0.011, 0.064, 0.017, 0.006, 0.001, 0.010, 0.151, 0.033, 0.031, 0.042, 0.044, 0.035, 0.021, 0.013, 0.035],
    'Glicose_Media': [6.006, 7.711, 9.085, 10.227, 12.006, 12.969, 14.340, 15.335, 16.152, 17.046, 16.877, 17.251, 16.030, 14.814, 15.116, 18.414, 17.510],
    'Glicose_Erro': [np.nan, 0.051, 0.008, 0.299, 0.112, 0.091, 0.081, 0.188, 0.430, 0.178, 0.329, 0.405, 0.453, 0.234, 0.303, 0.156, 0.463],
    'Xilose_Media': [3.150, 4.500, 5.059, 5.536, 6.229, 6.596, 7.256, 7.655, 7.969, 8.358, 8.162, 8.316, 7.723, 7.127, 7.202, 8.750, 8.262],
    'Xilose_Erro': [np.nan, 0.040, 0.014, 0.050, 0.076, 0.061, 0.017, 0.109, 0.194, 0.117, 0.139, 0.217, 0.216, 0.085, 0.141, 0.060, 0.223],
    'Experimento': ['Batelada 2'] * 17
}

exp3_data = {
    'Tempo': [0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24],
    'Celobiose_Media': [1.215, 1.450, 1.350, 1.320, 1.042, 1.354, 1.254, 1.200, 1.195, 1.020, 0.989, 0.992, 0.900, 0.911, 0.811, 0.790, 0.790],
    'Celobiose_Erro': [0.021, 0.012, 0.027, 0.037, 0.029, 0.011, 0.004, 0.002, 0.007, 0.006, 0.014, 0.043, 0.027, 0.009, 0.006, 0.027, 0.027],
    'Glicose_Media': [6.263, 8.483, 8.986, 10.660, 13.265, 13.369, 13.435, 13.607, 14.223, 13.496, 13.594, 13.531, 13.396, 14.519, 13.146, 13.655, 13.655],
    'Glicose_Erro': [0.048, 0.040, 0.088, 0.157, 0.166, 0.042, 0.086, 0.168, 0.076, 0.058, 0.218, 0.909, 0.288, 0.135, 0.300, 0.128, 0.128],
    'Xilose_Media': [3.069, 4.851, 4.913, 5.577, 6.996, 6.739, 6.710, 6.763, 6.963, 7.134, 7.148, 7.195, 6.727, 7.287, 6.717, 6.967, 6.967],
    'Xilose_Erro': [0.188, 0.049, 0.031, 0.076, 0.126, 0.031, 0.064, 0.058, 0.013, 0.075, 0.087, 0.403, 0.039, 0.038, 0.014, 0.172, 0.223],
    'Experimento': ['Batelada 3'] * 17
}

exp4_data = {
    'Tempo': [0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24],
    'Celobiose_Media': [0.708, 0.915, 0.893, 0.762, 0.964, 0.784, 0.870, 0.886, 0.869, 0.812, 0.783, 0.921, 0.794, 0.775, 0.785, 0.729, 0.784],
    'Celobiose_Erro': [0.021, 0.012, 0.027, 0.037, 0.029, 0.011, 0.004, 0.002, 0.007, 0.006, 0.014, 0.043, 0.027, 0.009, 0.006, 0.027, 0.027],
    'Glicose_Media': [6.885, 9.539, 10.610, 10.932, 12.455, 12.155, 12.979, 13.314, 13.510, 13.480, 14.337, 13.269, 13.440, 13.576, 14.284, 14.305, 15.027],
    'Glicose_Erro': [0.048, 0.040, 0.088, 0.157, 0.166, 0.042, 0.086, 0.168, 0.076, 0.058, 0.218, 0.909, 0.288, 0.135, 0.300, 0.128, 0.128],
    'Xilose_Media': [2.293, 4.851, 4.913, 5.577, 6.996, 6.739, 6.710, 6.763, 6.963, 7.134, 7.148, 7.195, 6.727, 7.287, 6.717, 6.967, 6.967],
    'Xilose_Erro': [0.188, 0.049, 0.031, 0.076, 0.126, 0.031, 0.064, 0.058, 0.013, 0.075, 0.087, 0.403, 0.039, 0.038, 0.014, 0.172, 0.223],
    'Experimento': ['Batelada 4'] * 17
}

# Consolidando em um único DataFrame
df = pd.concat([pd.DataFrame(exp1_data), pd.DataFrame(exp2_data), pd.DataFrame(exp3_data), pd.DataFrame(exp4_data)], ignore_index=True)

# ===== CONFIGURAÇÃO DOS GRÁFICOS =====
sns.set_theme(style="white") # Fundo limpo sem grid

# Lista de analitos (Nome, Coluna_Media, Coluna_Erro, Cor do gráfico)
analytes = [
    ('Glicose', 'Glicose_Media', 'Glicose_Erro', 'red'),
    ('Xilose', 'Xilose_Media', 'Xilose_Erro', 'magenta'),
    ('Celobiose', 'Celobiose_Media', 'Celobiose_Erro', 'green')
]

markers = ['o', 's', '^', 'D']
batches = ['Batelada 1', 'Batelada 2', 'Batelada 3', 'Batelada 4']

# Diferentes estilos de linha para cada batelada
linestyles = ['--', ':', '-.', (0, (3, 1, 1, 1))] 

# Loop para criar e SALVAR uma figura separada para cada analito
for name, col_mean, col_err, color in analytes:
    plt.figure(figsize=(8, 6))
    
    for i, batch in enumerate(batches):
        subset = df[df['Experimento'] == batch]
        
        plt.errorbar(subset['Tempo'], subset[col_mean], yerr=subset[col_err],
                     fmt=markers[i], label=batch, capsize=4,
                     color=color, alpha=0.7, markersize=7, 
                     linestyle=linestyles[i], linewidth=1.5)
    
    # Customização exclusiva do gráfico atual
    plt.title(f'{name} ', fontsize=14, fontweight='bold')
    plt.xlabel('Tempo (h)', fontsize=12)
    plt.ylabel('Concentração (g/L)', fontsize=12)
    plt.legend(title='Experimentos')
    
    # Adiciona limites ao eixo X para ter um respiro nas bordas
    plt.xlim(-1, 26) 
    
    plt.tight_layout()
    

    nome_arquivo = f'grafico_{name}.png'
    plt.savefig(nome_arquivo, dpi=1000, bbox_inches='tight')
    print(f'Gráfico salvo com sucesso: {nome_arquivo}')
    
    # Exibe a figura (opcional, pode remover ou comentar o plt.show() se quiser apenas gerar os arquivos sem abrir na tela)
    plt.show()