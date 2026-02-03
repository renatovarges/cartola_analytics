import pandas as pd
import sys
import os

# Adicionar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Carregar planilha
file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== AUDITORIA: Desarmes Cedidos LE - Coritiba ===\n")

# Carregar aba Por Jogo
df = pd.read_excel(file_path, sheet_name="Por jogo")

print(f"Total de linhas carregadas: {len(df)}")
print(f"Colunas disponíveis: {df.columns.tolist()}\n")

# Normalizar nomes de colunas
df.columns = df.columns.str.strip().str.upper()

# Identificar jogo Coritiba x Red Bull Bragantino
print("--- Identificando jogo Coritiba x Red Bull Bragantino ---")
coritiba_games = df[df['TIME'].str.contains('CORITIBA', case=False, na=False)]
print(f"Jogos do Coritiba encontrados: {len(coritiba_games)}")

# Filtrar jogo específico
jogo_coritiba_rbr = df[
    (df['TIME'].str.contains('CORITIBA', case=False, na=False)) &
    (df['ADVERSÁRIO'].str.contains('RED BULL|BRAGANTINO', case=False, na=False))
]

print(f"\nJogo Coritiba x RB Bragantino: {len(jogo_coritiba_rbr)} linhas")

if len(jogo_coritiba_rbr) > 0:
    print("\n--- Dados do jogo ---")
    print(jogo_coritiba_rbr[['NOME2', 'TIME', 'ADVERSÁRIO', 'POSREAL', 'DS', 'DE']].to_string())

# Agora vamos buscar os LATERAIS ESQUERDOS do RED BULL BRAGANTINO
# que jogaram CONTRA o Coritiba (esses são os "cedidos")
print("\n\n=== LATERAIS ESQUERDOS DO RED BULL BRAGANTINO (Adversário) ===")

rbr_vs_coritiba = df[
    (df['TIME'].str.contains('RED BULL|BRAGANTINO', case=False, na=False)) &
    (df['ADVERSÁRIO'].str.contains('CORITIBA', case=False, na=False))
]

print(f"Total de jogadores RBR vs Coritiba: {len(rbr_vs_coritiba)}")

# Filtrar por PosReal = 2.6 (Lateral Esquerdo)
le_rbr = rbr_vs_coritiba[rbr_vs_coritiba['POSREAL'] == 2.6]

print(f"\nLaterais Esquerdos (PosReal 2.6) do RBR: {len(le_rbr)}")

if len(le_rbr) > 0:
    print("\n--- Desarmes (DS) dos LE do RBR ---")
    print(le_rbr[['NOME2', 'TIME', 'ADVERSÁRIO', 'POSREAL', 'DS', 'DE', 'BÁSICA']].to_string())
    print(f"\n>>> TOTAL DS (Desarmes): {le_rbr['DS'].sum()}")
    print(f">>> TOTAL DE: {le_rbr['DE'].sum()}")
else:
    print("NENHUM Lateral Esquerdo encontrado!")
    
    # Verificar se há jogadores com outras posições
    print("\n--- Todas as posições do RBR neste jogo ---")
    print(rbr_vs_coritiba[['NOME2', 'POSREAL', 'DS', 'DE']].to_string())
