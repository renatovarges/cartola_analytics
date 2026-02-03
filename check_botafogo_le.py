import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

df = pd.read_excel(file_path, sheet_name="Por jogo")

print("=== VERIFICANDO LE DO BOTAFOGO ===\n")

botafogo = df[df['Time'].str.contains('Botafogo', case=False, na=False)]
le_botafogo = botafogo[botafogo['PosReal'] == 2.6]

print(f"LE do Botafogo: {len(le_botafogo)}")
if len(le_botafogo) > 0:
    print(le_botafogo[['Nome2', 'Adversário', 'DS', 'G', 'A', 'Básica']])
    print(f"\nSoma DS: {le_botafogo['DS'].sum()}")
