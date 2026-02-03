import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

df = pd.read_excel(file_path, sheet_name="Por jogo")

print("=== VERIFICAÇÃO: CRUZEIRO E CORITIBA TÊM LATERAIS? ===\n")

# Cruzeiro
cruzeiro = df[df['Time'].str.contains('Cruzeiro', case=False, na=False)]
print(f"Total de jogadores do Cruzeiro: {len(cruzeiro)}")

le_cruzeiro = cruzeiro[cruzeiro['PosReal'] == 2.6]
ld_cruzeiro = cruzeiro[cruzeiro['PosReal'] == 2.2]

print(f"  - Laterais Esquerdos (2.6): {len(le_cruzeiro)}")
print(f"  - Laterais Direitos (2.2): {len(ld_cruzeiro)}")

if len(le_cruzeiro) > 0:
    print("\n  LE do Cruzeiro:")
    print(le_cruzeiro[['Nome2', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

if len(ld_cruzeiro) > 0:
    print("\n  LD do Cruzeiro:")
    print(ld_cruzeiro[['Nome2', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

# Coritiba
print("\n" + "="*60 + "\n")
coritiba = df[df['Time'].str.contains('Coritiba', case=False, na=False)]
print(f"Total de jogadores do Coritiba: {len(coritiba)}")

le_coritiba = coritiba[coritiba['PosReal'] == 2.6]
ld_coritiba = coritiba[coritiba['PosReal'] == 2.2]

print(f"  - Laterais Esquerdos (2.6): {len(le_coritiba)}")
print(f"  - Laterais Direitos (2.2): {len(ld_coritiba)}")

if len(le_coritiba) > 0:
    print("\n  LE do Coritiba:")
    print(le_coritiba[['Nome2', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

if len(ld_coritiba) > 0:
    print("\n  LD do Coritiba:")
    print(ld_coritiba[['Nome2', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

print("\n" + "="*60)
print("CONCLUSÃO:")
if len(le_cruzeiro) == 0 and len(ld_cruzeiro) == 0:
    print("❌ CRUZEIRO NÃO TEM LATERAIS NA PLANILHA!")
if len(le_coritiba) == 0 and len(ld_coritiba) == 0:
    print("❌ CORITIBA NÃO TEM LATERAIS NA PLANILHA!")
    
if (len(le_cruzeiro) == 0 and len(ld_cruzeiro) == 0) and (len(le_coritiba) == 0 and len(ld_coritiba) == 0):
    print("\n⚠️ AMBOS OS TIMES NÃO TÊM LATERAIS!")
    print("Isso explica por que a linha está toda zerada.")
