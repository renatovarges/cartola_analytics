import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== INVESTIGAÇÃO COMPLETA: De onde vem o '4'? ===\n")

df = pd.read_excel(file_path, sheet_name="Por jogo")
df.columns = df.columns.str.strip().str.upper()

# Jogadores do RBR que jogaram contra Coritiba
rbr_vs_coritiba = df[
    (df['TIME'].str.contains('RED BULL|BRAGANTINO', case=False, na=False)) &
    (df['ADVERSÁRIO'].str.contains('CORITIBA', case=False, na=False))
]

print(f"Total de jogadores RBR vs Coritiba: {len(rbr_vs_coritiba)}\n")

# Mostrar TODOS os jogadores com seus desarmes
print("--- TODOS os jogadores do RBR neste jogo ---")
print(rbr_vs_coritiba[['NOME2', 'POSREAL', 'DS', 'DE']].to_string())

# Calcular soma total de DS
total_ds = rbr_vs_coritiba['DS'].sum()
print(f"\n>>> SOMA TOTAL DS de TODOS os jogadores do RBR: {total_ds}")

# Verificar se há algum jogador com DS = 4
jogadores_com_4_ds = rbr_vs_coritiba[rbr_vs_coritiba['DS'] == 4.0]
print(f"\n--- Jogadores com exatamente 4 desarmes ---")
if len(jogadores_com_4_ds) > 0:
    print(jogadores_com_4_ds[['NOME2', 'POSREAL', 'DS']].to_string())
else:
    print("Nenhum jogador tem exatamente 4 desarmes")

# Verificar se a lógica está somando posições erradas
print("\n--- Agrupamento por PosReal ---")
agrupado = rbr_vs_coritiba.groupby('POSREAL')['DS'].sum()
print(agrupado)

print("\n--- Verificando se há LD (2.2) sendo contado ---")
ld_rbr = rbr_vs_coritiba[rbr_vs_coritiba['POSREAL'] == 2.2]
if len(ld_rbr) > 0:
    print(ld_rbr[['NOME2', 'POSREAL', 'DS']].to_string())
    print(f"Total DS dos LD: {ld_rbr['DS'].sum()}")
else:
    print("Nenhum LD encontrado")
