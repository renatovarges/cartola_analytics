import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== RASTREAMENTO COMPLETO DO ENGINE ===\n")

# Carregar engine
engine = CartolaEngine(file_path)

# Adicionar prints de debug no método
# Vou simular manualmente o que o método faz

mandante = "Coritiba"  # Normalizado
visitante = "Red Bull Bragantino"
window_n = 5

df_all = engine.df_pj.copy()

print(f"Total de linhas no df_pj: {len(df_all)}")
print(f"Colunas: {df_all.columns.tolist()}\n")

# 1. Filtrar jogos do mandante
matches_man = df_all[df_all["TIME"] == mandante]
print(f"--- Jogos do {mandante} ---")
print(f"Total: {len(matches_man)}")

if len(matches_man) > 0:
    # 2. Pegar últimos 5 jogos (por MATCH_ID)
    match_dates = matches_man.groupby("MATCH_ID")["DATA"].first().sort_values().tail(window_n)
    selected_ids = match_dates.index.tolist()
    
    print(f"\nÚltimos {window_n} MATCH_IDs:")
    for mid in selected_ids:
        print(f"  - {mid}")
    
    # 3. CDF: Stats dos Adversários nesses jogos
    print(f"\n--- CDF: Adversários do {mandante} nesses jogos ---")
    df_opp_games = df_all[(df_all["MATCH_ID"].isin(selected_ids)) & (df_all["TIME"] != mandante)]
    
    print(f"Total de jogadores dos adversários: {len(df_opp_games)}")
    print(f"\nTimes adversários:")
    print(df_opp_games['TIME'].value_counts())
    
    # 4. Filtrar apenas Laterais Esquerdos (PosReal 2.6)
    le_opp = df_opp_games[df_opp_games['POS_REAL'].apply(lambda x: abs(float(x) - 2.6) < 0.01 if pd.notna(x) else False)]
    
    print(f"\n--- Laterais Esquerdos dos adversários ---")
    print(f"Total: {len(le_opp)}")
    
    if len(le_opp) > 0:
        print("\nJogadores:")
        print(le_opp[['NOME', 'TIME', 'POS_REAL', 'DS']].to_string())
        print(f"\nSoma de DS: {le_opp['DS'].sum()}")
    else:
        print("Nenhum LE encontrado!")
    
    # 5. Chamar o método real
    print(f"\n--- Resultado do método get_laterais_aggregated ---")
    cdf_stats = engine.get_laterais_aggregated(df_opp_games, 0)
    print(f"LE_DE: {cdf_stats['LE_DE']}")
    print(f"LD_DE: {cdf_stats['LD_DE']}")
