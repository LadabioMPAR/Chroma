import matplotlib.pyplot as plt
import numpy as np
import random

# --- Configurações da Simulação ---
N_PARTICULAS = 500  # Número total de partículas a agregar
TAMANHO_GRADE = 100 # Dimensão da grade (NxN)
ATUALIZAR_GRAFICO = 1 # Atualizar o gráfico a cada X partículas grudadas

# Inicializar a grade vazia
grade = np.zeros((TAMANHO_GRADE, TAMANHO_GRADE))

# Colocar a Semente no centro
centro = TAMANHO_GRADE // 2
grade[centro, centro] = 1
aglomerado_x = [centro]
aglomerado_y = [centro]

# Definir possíveis movimentos (Cima, Baixo, Esq, Dir)
movimentos = [(0, 1), (0, -1), (1, 0), (-1, 0)]

# --- Configuração do Gráfico ---
plt.figure(figsize=(8, 8))
plt.title(f"Simulação DLA - {N_PARTICULAS} Partículas")
plt.axis('off')

print("Iniciando a simulação...")

# --- Loop Principal de Partículas ---
for i in range(N_PARTICULAS):
    
    # Define o raio de lançamento um pouco maior que o aglomerado atual
    raio_max = 0
    for x, y in zip(aglomerado_x, aglomerado_y):
        raio = np.sqrt((x - centro)**2 + (y - centro)**2)
        if raio > raio_max:
            raio_max = raio
    
    # Partícula nasce na borda de um círculo de lançamento
    angulo = random.uniform(0, 2 * np.pi)
    raio_lançamento = raio_max + 2
    
    px = int(centro + raio_lançamento * np.cos(angulo))
    py = int(centro + raio_lançamento * np.sin(angulo))
    
    # Garantir que não nasça fora da grade
    px = max(1, min(TAMANHO_GRADE - 2, px))
    py = max(1, min(TAMANHO_GRADE - 2, py))
    
    grudou = False
    passos = 0
    MAX_PASSOS = TAMANHO_GRADE * 10 # Evitar loops infinitos

    # --- Loop da Caminhada Aleatória da Partícula ---
    while not grudou and passos < MAX_PASSOS:
        # Escolher movimento
        dx, dy = random.choice(movimentos)
        
        # Próxima posição candidata
        nova_px = px + dx
        nova_py = py + dy
        
        # Verificar fronteiras da grade
        if not (0 <= nova_px < TAMANHO_GRADE and 0 <= nova_py < TAMANHO_GRADE):
            break # Partícula fugiu da grade, lança outra
            
        # Verificar vizinhos (se encostou em algo grudado)
        # Checagem simples nas 4 direções principais (pode ser expandida para 8)
        vizinhos = [
            (nova_px + 1, nova_py), (nova_px - 1, nova_py),
            (nova_px, nova_py + 1), (nova_px, nova_py - 1)
        ]
        
        for vx, vy in vizinhos:
            if 0 <= vx < TAMANHO_GRADE and 0 <= vy < TAMANHO_GRADE:
                if grade[vx, vy] == 1:
                    grade[nova_px, nova_py] = 1 # Gruda!
                    aglomerado_x.append(nova_px)
                    aglomerado_y.append(nova_py)
                    grudou = True
                    break
        
        if grudou:
            break
            
        # Se não grudou, atualiza posição e continua andando
        px, py = nova_px, nova_py
        passos += 1
        
    # --- Atualização Visual ---
    if (i + 1) % ATUALIZAR_GRAFICO == 0 or (i + 1) == N_PARTICULAS:
        plt.imshow(grade, cmap='Blues', origin='lower')
        plt.draw()
        plt.pause(0.0000000001) # Pausa curta para a animação

print("Simulação concluída!")
plt.show()