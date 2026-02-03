import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== DEBUG PROFUNDO: Lógica de Agregação ===\n")

df = pd.read_excel(file_path, sheet_name="Por jogo")
df.columns = df.columns.str.strip().str.upper()

# Simular o que o engine faz
mandante = "CORITIBA"
window_n = 5

# 1. Filtrar jogos do Coritiba em casa
matches_man = df[df["TIME"] == mandante]
print(f"Total de jogos do {mandante}: {len(matches_man)}")

# 2. Pegar últimos 5 jogos
# (simplificado - sem MATCH_ID por enquanto)
print(f"\n--- Últimos {window_n} adversários do {mandante} ---")
adversarios = matches_man['ADVERSÁRIO'].unique()
print(adversarios)

# 3. O que o código ATUAL faz:
# Pega TODOS os jogadores de TODOS os adversários nesses jogos
print(f"\n--- O que o código ATUAL faz (ERRADO) ---")
print("Pega TODOS os jogadores dos adversários, de TODOS os jogos!")

# Exemplo: Se Coritiba jogou contra RBR, Vasco, Santos, Palmeiras, Athletico
# O código pega:
# - TODOS os jogadores do RBR (incluindo de outros jogos)
# - TODOS os jogadores do Vasco (incluindo de outros jogos)
# - etc.

# E SOMA TUDO JUNTO!

print("\n--- Exemplo com RB Bragantino ---")
rbr_all = df[df['TIME'].str.contains('RED BULL|BRAGANTINO', case=False, na=False)]
print(f"Total de jogadores do RBR em TODOS os jogos: {len(rbr_all)}")
print(f"Soma de DS de TODOS: {rbr_all['DS'].sum()}")

rbr_vs_coritiba = df[
    (df['TIME'].str.contains('RED BULL|BRAGANTINO', case=False, na=False)) &
    (df['ADVERSÁRIO'].str.contains('CORITIBA', case=False, na=False))
]
print(f"\nTotal de jogadores do RBR APENAS vs Coritiba: {len(rbr_vs_coritiba)}")
print(f"Soma de DS apenas vs Coritiba: {rbr_vs_coritiba['DS'].sum()}")

print("\n--- CONCLUSÃO ---")
print("O engine está somando desarmes de jogadores de MÚLTIPLOS JOGOS,")
print("não apenas do jogo específico contra o Coritiba!")
print("\nIsso explica por que aparecem valores aleatórios como '4'.")
