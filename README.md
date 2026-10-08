# FunkGen - Gerador de Beats de Funk de BH com PDFA

Este projeto utiliza técnicas de Inferência Gramatical e Aprendizado de Máquina para analisar, aprender e gerar novos beats de **Funk de Belo Horizonte**. A partir de um dataset de arquivos MIDI elaborados por produtores e DJs reais, o sistema treina um Autômato Finito Determinístico Probabilístico (PDFA) usando o [FlexFringe](https://github.com/gitcst/flexfringe) e, em seguida, utiliza o modelo treinado para compor novos padrões rítmicos autênticos.

## Estrutura do Projeto

Abaixo está a organização dos diretórios e arquivos da aplicação:

```text
.
├── dataset/              # Dataset com arquivos .mid usados no treinamento
├── beats/                # Arquivos MIDI (.mid) virgens gerados pelo algoritmo
├── imgs/                 # Imagens e grafos (.dot/.png) do autômato gerado pelo FlexFringe
├── trained/              # Arquivos de saída do aprendizado pelo FlexFringe
├── prod/                 # Projeto do Ableton Live 11 com a renderização dos beats gerados
├── conf.ini              # Hiperparâmetros configurados para o treinamento no FlexFringe
├── pre_proc.py           # Script de pré-processamento (Quantização 1/16, Mapeamento -> .aabb)
├── generate_music.py     # Script que lê o modelo treinado e gera os novos beats
└── symbol_mapping.txt    # Dicionário de mapeamento do alfabeto (ex: K=Kick, S=Snare, P=Prato)
```

## Pipeline de Funcionamento

O projeto é dividido em quatro etapas principais:

### 1. Pré-processamento (`pre_proc.py`)
Lê os arquivos MIDI da pasta `dataset/`, quantiza os eventos musicais para uma grade de semicolcheias (1/16) e mapeia as notas (bumbos, caixas, pratos) para um alfabeto discreto usando as regras definidas em `symbol_mapping.txt`. O resultado é exportado para um arquivo de sequências `.aabb` que o FlexFringe consegue ler.

### 2. Treinamento do Modelo (FlexFringe)
O FlexFringe consome o arquivo `.aabb` gerado na etapa anterior juntamente com o arquivo `conf.ini` (onde estão definidos parâmetros como heurísticas de merge, limiares de probabilidade, etc.). 
* **Saída:** O modelo estrutural salvo na pasta `trained/` e uma representação visual do autômato gerado na pasta `imgs/`.

### 3. Geração de Música (`generate_music.py`)
Este script carrega o PDFA treinado e realiza passeios aleatórios (random walks) pelo grafo, respeitando as probabilidades de transição aprendidas e o parâmetro de temperatura (CHAOS). Quanto maior a temperatura, mais diversas e criativas serão as batidas geradas. A sequência de caracteres resultante é então convertida de volta para o formato `.mid` e salva na pasta `beats/`.

### 4. Produção Final (`prod/`)
Como o MIDI gerado possui marcações literais e matemáticas (sem "groove" humano), os melhores resultados da pasta `beats/` foram importados para um projeto no **Ableton Live 11**. Nesta etapa, um produtor musical aplicou samples reais, processamento de áudio, *swing* e mixagem.

## Como Executar

**Pré-requisitos:**
* Python 3.8+
* Biblioteca `mido` (`pip install mido`)
* FlexFringe (opcional - apenas se quiser treinar novos modelos)

### Passo a passo

Geração do Modelo:

1. **Gere os dados de treinamento:**
   ```bash
   python pre_proc.py
   ```
   *(Isso lerá a pasta `dataset/` e gerará o arquivo `.aabb` raiz)*

2. **Treine o autômato (exemplo via CLI do FlexFringe):**
   ```bash
   flexfringe --ini conf.ini dataset_funk.aabb 
   ```
   *(Mova os arquivos resultantes para a pasta `trained/` e as imagens para `imgs/`)*

Geração de Beats:

1. **Gere novos beats:**
   usage: generate_music.py [-h] [-n N] [--seed SEED] [--mapping MAPPING] model [chaos]

   ```bash
   python generate_music.py trained/dataset_funk.aabb.ff.final.json CHAOS -n N --seed SEED 
   ```
   *(Verifique a pasta `beats/` para ouvir as novas criações)*

## Notas de Mapeamento (Alfabeto)
O arquivo `symbol_mapping.txt` dita a conversão para PDFA. Um exemplo típico de Funk de BH utilizado neste projeto:
* `K` = Kick (Grave/Bumbo)
* `S` = Snare (Caixa/Estalo)
* `P` = Prato / Percussão aguda
* `B` = Beatbox / Tom
* `.` = Silêncio (Rest)
*(Notas simultâneas são agrupadas em ordem alfabética, ex: `KP` para Kick e Prato juntos).*
