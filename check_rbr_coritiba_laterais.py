import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

df = pd.read_excel(file_path, sheet_name="Por jogo")

print("=== LATERAIS DO RBR vs CORITIBA ===\n")

# Filtrar RBR vs Coritiba
rbr_vs_cor = df[
    (df['Time'].str.contains('Red Bull|Bragantino', case=False, na=False)) &
    (df['Adversário'].str.contains('Coritiba', case=False, na=False))
]

print(f"Total de jogadores do RBR vs Coritiba: {len(rbr_vs_cor)}\n")

# Separar por posição
le = rbr_vs_cor[rbr_vs_cor['PosReal'] == 2.6]
ld = rbr_vs_cor[rbr_vs_cor['PosReal'] == 2.2]

print("--- LATERAIS ESQUERDOS (PosReal 2.6) ---")
if len(le) > 0:
    print(le[['Nome2', 'PosReal', 'DS', 'G', 'A', 'Básica']].to_string())
    print(f"\nTotal DS: {le['DS'].sum()}")
else:
    print("NENHUM LE encontrado!")

print("\n--- LATERAIS DIREITOS (PosReal 2.2) ---")
if len(ld) > 0:
    print(ld[['Nome2', 'PosReal', 'DS', 'G', 'A', 'Básica']].to_string())
    print(f"\nTotal DS: {ld['DS'].sum()}")
else:
    print("NENHUM LD encontrado!")

# Verificar TODAS as posições para entender melhor
print("\n--- TODAS AS POSIÇÕES (RBR vs Coritiba) ---")
print(rbr_vs_cor.groupby('PosReal')['DS'].agg(['count', 'sum']))

# Agora verificar o INVERSO: Coritiba vs RBR
print("\n\n=== LATERAIS DO CORITIBA vs RBR ===\n")

cor_vs_rbr = df[
    (df['Time'].str.contains('Coritiba', case=False, na=False)) &
    (df['Adversário'].str.contains('Red Bull|Bragantino', case=False, na=False))
]

print(f"Total de jogadores do Coritiba vs RBR: {len(cor_vs_rbr)}\n")

le_cor = cor_vs_rbr[cor_vs_rbr['PosReal'] == 2.6]
ld_cor = cor_vs_rbr[cor_vs_rbr['PosReal'] == 2.2]

print("--- LATERAIS ESQUERDOS (PosReal 2.6) ---")
if len(le_cor) > 0:
    print(le_cor[['Nome2', 'PosReal', 'DS', 'G', 'A', 'Básica']].to_string())
    print(f"\nTotal DS: {le_cor['DS'].sum()}")
else:
    print("NENHUM LE encontrado!")

print("\n--- LATERAIS DIREITOS (PosReal 2.2) ---")
if len(ld_cor) > 0:
    print(ld_cor[['Nome2', 'PosReal', 'DS', 'G', 'A', 'Básica']].to_string())
    print(f"\nTotal DS: {ld_cor['DS'].sum()}")
else:
    print("NENHUM LD encontrado!")
