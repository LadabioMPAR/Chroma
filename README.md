# Chroma

Ferramentas para **integração e cálculo de áreas de cromatogramas de HPLC** —
da leitura dos arquivos brutos do equipamento até a concentração dos analitos.

Os cromatogramas trafegam como CSV com duas colunas, `time` e `signal`. Cada
ferramenta em `scripts/` é **independente**: faz uma coisa, lê e escreve CSVs, e
é configurada por um bloco próprio do [`config.toml`](config.toml). Não existe
uma ordem obrigatória — você compõe as que precisar. A biblioteca `chroma/`
guarda a matemática compartilhada.

## Instalação

Já existe um `venv/` no repositório. Para recriar do zero:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Não há dependência nova para a configuração: o `config.toml` é lido com
`tomllib`, da biblioteca padrão (Python 3.11+).

## As ferramentas

| Ferramenta | O que faz | Bloco do config |
|---|---|---|
| `ler_cdf.py` | Converte `.cdf` do HPLC em CSV + PNG + resumo | `[paths]` |
| `corrigir_baseline.py` | Corrige a linha de base (linear ou BEADS) | `[baseline]` |
| `ajuste_individual.py` | Estima áreas ajustando cada pico (parâmetros livres, qualquer modelo) | `[individual_fit]` |
| `analisar.py` | Calibra k/θ nos padrões e analisa amostras com eles travados | `[analysis]` |
| `curva_calibracao.py` | Monta retas de calibração por analito | `[calibration]` |
| `calcular_concentracoes.py` | Varre uma pasta e calcula concentrações via as curvas | `[quantify]` |

Todos os comandos assumem o `venv` ativado (ou use `./venv/bin/python`).

### `ler_cdf.py` — converter CDF em CSV
```bash
python scripts/ler_cdf.py
```
Lê `data/raw/*.cdf` e gera, por arquivo, um CSV em `data/chromatograms/`, um PNG
em `outputs/plots/` e uma linha no resumo (`outputs/results/resumo.csv`) com os
metadados da injeção.

### `corrigir_baseline.py` — corrigir linha de base
```bash
python scripts/corrigir_baseline.py
```
Corrige a linha de base de espectros específicos — indicados por um glob ou por
uma lista explícita de arquivos — pelo método `linear` (reta por mínimos
quadrados) ou `beads` (linha de base suave, iterativa). Salva CSVs em que a
coluna `signal` já vem corrigida (drop-in para as outras ferramentas), com o
sinal original e a baseline guardados como colunas extras, mais um gráfico.

### `ajuste_individual.py` — estimar áreas (ajuste livre)
```bash
python scripts/ajuste_individual.py
```
Detecta os picos de cada cromatograma e ajusta cada um com **todos os parâmetros
livres**, exportando os parâmetros do modelo + **área** + R² por pico. O modelo
vem de `[individual_fit].model` — `gamma`, `gaussian` ou qualquer outro
registrado em [`chroma/models.py`](chroma/models.py); **não está preso ao gamma**.
As colunas de saída acompanham o modelo escolhido (gamma → `A, t0, k, theta`;
gaussian → `A, mu, sigma`).

### `analisar.py` — calibrar e analisar (ajuste travado)
```bash
python scripts/analisar.py
```
Estima **k e theta** a partir dos padrões (`standards_glob`) com um ajuste global
— um k e um theta comuns a todos os cromatogramas — e depois analisa as amostras
(`samples_glob`) com esses valores **travados**, ajustando só A e t0 de cada pico
e exportando as áreas. Use `k`/`theta` = `"auto"` para estimar, ou escreva os
números para reaproveitar uma calibração anterior. Esta ferramenta usa o gamma.

### `curva_calibracao.py` — curvas de calibração
```bash
python scripts/curva_calibracao.py
```
Monta uma reta **concentração = a·área + b** para cada analito (b = 0 por
padrão; `fit_intercept = true` estima b). Lê as áreas de um CSV já gerado por
`ajuste_individual` ou `analisar`; para cada analito você informa o nome, o tempo
do pico e os pontos da curva (cada padrão com sua concentração). A cada execução
gera um gráfico por analito, a tabela `calibracao.csv` e o **`calibracao.txt`**
(tab-delimitado), este último pensado para outro script consumir as curvas.

### `calcular_concentracoes.py` — quantificar uma pasta
```bash
python scripts/calcular_concentracoes.py
```
Varre `input_dir`, ajusta os picos de cada amostra e calcula a concentração de
cada analito aplicando as curvas de `curves_txt` (o `calibracao.txt`): casa o
pico mais próximo do tempo de retenção da curva e aplica `conc = a·área + b`.
Retorna uma tabela com uma linha por amostra e uma coluna por analito; `NaN`
quando o pico do analito não é encontrado.

## Exemplo: de CDF a concentrações

As ferramentas são independentes — este é apenas **um encadeamento comum**, com
saídas reais dos padrões em `data/chromatograms/pad_e09`.

**1. Ler os arquivos brutos** (`[paths]`)
```bash
python scripts/ler_cdf.py
```
```
Encontrados 12 arquivos .cdf em 'data/raw'.
- Resumo:        outputs/results/resumo.csv
- Cromatogramas: data/chromatograms/
```

**2. Estimar as áreas dos picos** (`[individual_fit].input_dir`)
```bash
python scripts/ajuste_individual.py
```
Trecho do `outputs/results/parametros_ajuste_gamma_pad_e09.csv` (só as linhas da
glicose, valores truncados):
```
arquivo,tempo_pico,A,t0,k,theta,area,R2
Glic_3gl_5.csv,11.4,2.824181,10.98652,10.0,0.043144,2.824181,0.998869
Glic_3gl_10.csv,11.4,6.055081,10.98888,10.0,0.043438,6.055081,0.998925
Glic_3gl_20.csv,11.4,12.307122,11.00625,10.0,0.043911,12.307122,0.999352
Glic_3gl_40.csv,11.4,25.019934,11.01316,10.0,0.045407,25.019934,0.998984
```

**3. Montar as curvas de calibração** (`[calibration]`, apontando `areas_csv`
para o CSV do passo anterior e listando os analitos com seus padrões)
```bash
python scripts/curva_calibracao.py
```
```
  [Glicose]    conc = 1.6076·área + 0   R²=0.9995  (n=4)
  [Celobiose]  conc = 4.7656·área + 0   R²=0.9991  (n=4)
  [Xilose]     conc = 5.0163·área + 0   R²=0.9999  (n=4)
```
Gera também `outputs/results/calibracao.txt`:
```
# Curvas de calibracao (Chroma)
# modelo: concentracao = a * area + b
# colunas (separadas por TAB): analito	tempo_pico	a	b	R2	n_pontos
Glicose	11.4	1.607599711	0	0.99947451	4
Celobiose	9.3	4.765622934	0	0.9991092308	4
Xilose	12.2	5.016318101	0	0.9998606683	4
```

**4. Calcular as concentrações de uma pasta** (`[quantify]`, apontando
`curves_txt` para o txt acima)
```bash
python scripts/calcular_concentracoes.py
```
```
         arquivo   Glicose  Celobiose    Xilose
 Glic_3gl_5.csv   4.540153        NaN       NaN
 Glic_3gl_10.csv  9.734146        NaN       NaN
 Glic_3gl_20.csv 19.784925        NaN       NaN
 Glic_3gl_40.csv 40.222039        NaN       NaN
Celob_1gl_10.csv       NaN   9.635539       NaN
  xil_1gl_20.csv       NaN        NaN 20.058689
```
(Aqui as amostras são os próprios padrões, por isso as concentrações
reproduzem os valores nominais 5/10/20/40 — um bom teste de sanidade.)

## Estrutura do repositório

```
chroma/            biblioteca (a matemática vive aqui)
  config.py          leitura do config.toml e resolução de caminhos
  models.py          modelos de pico (registro plugável; gamma + gaussian)
  io.py              leitura de CDF, leitura/escrita de CSV de cromatograma
  peaks.py           detecção de picos (presets: prominence e relative_height)
  baseline.py        correção de linha de base (linear e BEADS)
  fitting.py         ajuste individual por pico (livre ou com k/theta travados)
  fitting_global.py  ajuste global compartilhando k e theta (padrões)
  analysis.py        calibrar (k,theta) + analisar amostras travadas
  calibration.py     curvas de calibração lineares + aplicação das curvas
  plotting.py        gráficos de cromatograma, ajuste, resíduos, baseline e calibração
scripts/           as 6 ferramentas independentes
config.toml        TODOS os parâmetros e pastas ficam aqui
data/
  raw/               arquivos .cdf do HPLC
  chromatograms/     CSVs (time, signal)
outputs/           tudo que é gerado (plots + results); não versionado
archive/           scripts e saídas antigas, preservados fora do caminho
exporter/          ferramenta separada de monitoramento do HPLC
```

## Modelos de pico

Os modelos ficam em [`chroma/models.py`](chroma/models.py) num **registro**.
Hoje há `gamma` (padrão) e `gaussian`. Para adicionar um novo (p.ex. EMG), crie
uma subclasse de `PeakModel` decorada com `@register_model("nome")`, implemente
`function`, `initial_guess` e `bounds`, e selecione-o pelo campo `model` do
`config.toml`:

```python
@register_model("emg")
class ExpModGaussian(PeakModel):
    param_names = ("A", "mu", "sigma", "tau")
    def function(self, t, A, mu, sigma, tau):
        ...
```

O `ajuste_individual` funciona com qualquer modelo registrado; o `analisar`
(ajuste global com k/θ travados) usa o gamma.

## Configuração

Todos os parâmetros vivem no [`config.toml`](config.toml), um bloco por
ferramenta, com os caminhos relativos resolvidos a partir da raiz do repositório.
Os comentários do arquivo explicam cada campo.

> **Nota:** `exporter/credenciais-api.json` contém credenciais e **não é
> versionado** (está no `.gitignore`).
