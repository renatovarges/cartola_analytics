import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

df = pd.read_excel(file_path, sheet_name="Por jogo")

print("=== VERIFICAÇÃO DE LATERAIS NA PLANILHA ===\n")

# Verificar quantos laterais existem
le = df[df['PosReal'] == 2.6]
ld = df[df['PosReal'] == 2.2]

print(f"Laterais Esquerdos (PosReal 2.6): {len(le)}")
print(f"Laterais Direitos (PosReal 2.2): {len(ld)}")

if len(le) > 0:
    print("\n--- Laterais Esquerdos ---")
    print(le[['Nome2', 'Time', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

if len(ld) > 0:
    print("\n--- Laterais Direitos ---")
    print(ld[['Nome2', 'Time', 'Adversário', 'DS', 'G', 'A', 'Básica']].to_string())

if len(le) == 0 and len(ld) == 0:
    print("\n❌ NÃO HÁ NENHUM LATERAL NA PLANILHA!")
    print("\n--- Verificando todas as posições ---")
    print(df['PosReal'].value_counts().sort_index())
