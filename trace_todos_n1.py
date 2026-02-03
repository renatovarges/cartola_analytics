import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

print("=== RASTREAMENTO COMPLETO: FILTRO TODAS, N=1 ===\n")

engine = CartolaEngine(file_path)

# Simular EXATAMENTE o que o usuário faz:
# Filtro: TODAS (mando_mode="TODOS")
# N: 1 (window_n=1)
# Jogo: Cruzeiro x Coritiba (Rodada 2)

mandante = "CRUZEIRO"
visitante = "CORITIBA"
window_n = 1
mando_mode = "TODOS"  # ← FILTRO TODAS!

print(f"Mandante: {mandante}")
print(f"Visitante: {visitante}")
print(f"Window N: {window_n}")
print(f"Mando Mode: {mando_mode}\n")

# Chamar o método
result = engine.generate_laterais_table(mandante, visitante, window_n=window_n, mando_mode=mando_mode)

print("--- RESULTADO DO ENGINE ---")
print(f"CDF_LE_DE: {result['CDF_LE_DE']}")
print(f"CDF_LD_DE: {result['CDF_LD_DE']}")
print(f"CDC_LE_DE: {result['CDC_LE_DE']}")
print(f"CDC_LD_DE: {result['CDC_LD_DE']}")

print("\n--- VALORES ESPERADOS (da planilha) ---")
print("Cruzeiro (mandante):")
print("  - LE: Kaiki Bruno vs Botafogo, DS=0")
print("  - LD: Fagner vs Botafogo, DS=1")
print("\nCoritiba (visitante):")
print("  - LE: NENHUM")
print("  - LD: Tinga vs RBR, DS=3")

print("\n--- COMPARAÇÃO ---")
print(f"COC_LD_DE deveria ser: 1 (Fagner)")
print(f"COC_LD_DE retornado: {result['COC_LD_DE']}")

print(f"\nCDC_LD_DE deveria ser: 3 (Tinga)")
print(f"CDC_LD_DE retornado: {result['CDC_LD_DE']}")

# Agora vou debugar DENTRO do método para ver o que está acontecendo
print("\n" + "="*60)
print("DEBUGANDO INTERNAMENTE...")
print("="*60 + "\n")

# Replicar a lógica do método manualmente
df_all = engine.df_pj.copy()

# 1. Filtrar jogos do Cruzeiro
matches_man = df_all[df_all["TIME"] == mandante]
print(f"Jogos do {mandante}: {len(matches_man)}")

if len(matches_man) > 0:
    # Pegar último jogo (N=1)
    match_dates = matches_man.groupby("MATCH_ID")["DATA"].first().sort_values().tail(window_n)
    selected_ids = match_dates.index.tolist()
    
    print(f"MATCH_IDs selecionados: {selected_ids}\n")
    
    # COC: Stats do Cruzeiro
    df_man_games = df_all[(df_all["MATCH_ID"].isin(selected_ids)) & (df_all["TIME"] == mandante)]
    print(f"Jogadores do Cruzeiro nesses jogos: {len(df_man_games)}")
    
    # Filtrar LD
    ld_cruzeiro = df_man_games[df_man_games['POS_REAL'] == 2.2]
    print(f"LD do Cruzeiro: {len(ld_cruzeiro)}")
    if len(ld_cruzeiro) > 0:
        print(ld_cruzeiro[['NOME', 'POS_REAL', 'DS']])
        print(f"Soma DS: {ld_cruzeiro['DS'].sum()}")
    
    # CDF: Stats dos Adversários
    df_opp_games = df_all[(df_all["MATCH_ID"].isin(selected_ids)) & (df_all["TIME"] != mandante)]
    print(f"\nJogadores dos ADVERSÁRIOS nesses jogos: {len(df_opp_games)}")
    print(f"Times adversários: {df_opp_games['TIME'].unique()}")
    
    # Filtrar LD dos adversários
    ld_adv = df_opp_games[df_opp_games['POS_REAL'] == 2.2]
    print(f"\nLD dos adversários: {len(ld_adv)}")
    if len(ld_adv) > 0:
        print(ld_adv[['NOME', 'TIME', 'POS_REAL', 'DS']])
        print(f"Soma DS: {ld_adv['DS'].sum()}")
