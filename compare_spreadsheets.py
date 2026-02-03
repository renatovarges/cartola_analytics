import pandas as pd

file1 = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
file2 = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== COMPARAÇÃO DE PLANILHAS ===\n")

df1 = pd.read_excel(file1, sheet_name="Por jogo")
df2 = pd.read_excel(file2, sheet_name="Por jogo")

print(f"Scouts_Reorganizado.xlsx: {len(df1)} linhas")
print(f"API CARTOLA RODADA 1.xlsx: {len(df2)} linhas")

print("\n--- Times em Scouts_Reorganizado ---")
times1 = df1['Time'].unique()
print(f"Total: {len(times1)}")
for t in sorted(times1):
    print(f"  - {t}")

print("\n--- Times em API CARTOLA RODADA 1 ---")
times2 = df2['Time'].unique()
print(f"Total: {len(times2)}")
for t in sorted(times2):
    print(f"  - {t}")

print("\n--- Verificando Coritiba ---")
coritiba1 = df1[df1['Time'].str.contains('Coritiba', case=False, na=False)]
coritiba2 = df2[df2['Time'].str.contains('Coritiba', case=False, na=False)]

print(f"Scouts_Reorganizado: {len(coritiba1)} jogadores")
print(f"API CARTOLA RODADA 1: {len(coritiba2)} jogadores")

if len(coritiba1) > 0:
    print("\nPrimeiros jogadores (Scouts_Reorganizado):")
    print(coritiba1[['Nome2', 'Time', 'Adversário']].head())
