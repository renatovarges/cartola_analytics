import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import pandas as pd

# Usar a MESMA planilha que o Streamlit usa
file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

print("=== TESTE FINAL COM PLANILHA CORRETA ===\n")

engine = CartolaEngine(file_path)

# Testar o método completo
result = engine.generate_laterais_table("Coritiba", "Red Bull Bragantino", window_n=5, mando_mode="POR_MANDO")

print("Resultado do generate_laterais_table:")
print(f"\nCDF_LE_DE (Desarmes cedidos LE): {result['CDF_LE_DE']}")
print(f"CDF_LD_DE (Desarmes cedidos LD): {result['CDF_LD_DE']}")

# Verificar o df_pj
print(f"\n--- Verificação do df_pj ---")
print(f"Total de linhas: {len(engine.df_pj)}")

coritiba_games = engine.df_pj[engine.df_pj['TIME'] == 'Coritiba']
print(f"Jogos do Coritiba: {len(coritiba_games)}")

if len(coritiba_games) == 0:
    print("\n❌ PROBLEMA: df_pj não tem jogos do Coritiba!")
    print("\nTimes únicos no df_pj:")
    print(engine.df_pj['TIME'].unique())
else:
    print("\n✓ df_pj tem jogos do Coritiba")
    
    # Debugar o método get_laterais_aggregated
    print("\n--- Debug get_laterais_aggregated ---")
    
    # Simular o que generate_laterais_table faz
    matches_man = engine.df_pj[engine.df_pj["TIME"] == "Coritiba"]
    match_dates = matches_man.groupby("MATCH_ID")["DATA"].first().sort_values().tail(5)
    selected_ids = match_dates.index.tolist()
    
    print(f"MATCH_IDs selecionados: {selected_ids}")
    
    # CDF: Adversários
    df_opp_games = engine.df_pj[(engine.df_pj["MATCH_ID"].isin(selected_ids)) & (engine.df_pj["TIME"] != "Coritiba")]
    
    print(f"\nTotal de jogadores dos adversários: {len(df_opp_games)}")
    print(f"Times: {df_opp_games['TIME'].unique()}")
    
    # Filtrar LE
    le_opp = df_opp_games[df_opp_games['POS_REAL'].apply(lambda x: abs(float(x) - 2.6) < 0.01 if pd.notna(x) else False)]
    print(f"\nLaterais Esquerdos: {len(le_opp)}")
    
    if len(le_opp) > 0:
        print(le_opp[['NOME', 'TIME', 'POS_REAL', 'DS']].to_string())
        print(f"\nSoma DS: {le_opp['DS'].sum()}")
