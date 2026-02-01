from src import loader
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
datasets = loader.load_excel_data(file_path)
df = datasets["POR_JOGO"]

players_to_check = ["EVERTON RIBEIRO", "ARRASCAETA", "GARRO", "RAPHAEL VEIGA"]

print("--- Verificando Posições ---")
for player in players_to_check:
    # Busca parcial
    res = df[df["NOME"].str.contains(player, na=False)]
    if not res.empty:
        print(f"\n{player}:")
        print(res[["NOME", "TIME", "POSICAO"]].head(1).to_string(index=False))
    else:
        print(f"\n{player}: NÃO ENCONTRADO")
