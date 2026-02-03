import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

df = pd.read_excel(file_path, sheet_name="Por jogo")
df.columns = df.columns.str.strip().str.upper()

print("=== VERIFICAÇÃO DE NOMES DE TIMES ===\n")

# Listar todos os times únicos
times_unicos = df['TIME'].unique()
print(f"Total de times na planilha: {len(times_unicos)}")
print("\nTimes encontrados:")
for time in sorted(times_unicos):
    print(f"  - {time}")

print("\n--- Procurando por 'CORITIBA' ---")
coritiba_matches = df[df['TIME'].str.contains('CORITIBA', case=False, na=False)]
print(f"Jogos encontrados: {len(coritiba_matches)}")

if len(coritiba_matches) > 0:
    print("\nPrimeiras linhas:")
    print(coritiba_matches[['TIME', 'ADVERSÁRIO', 'NOME2']].head())
else:
    print("\nNENHUM jogo encontrado!")
    print("\nVerificando variações:")
    for time in times_unicos:
        if 'CORIT' in time.upper():
            print(f"  Encontrado: '{time}'")
