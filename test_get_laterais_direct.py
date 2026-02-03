import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

print("=== TESTE DIRETO DA FUNÇÃO get_laterais_aggregated ===\n")

engine = CartolaEngine(file_path)

# Criar um DataFrame de teste com jogadores do RBR vs Coritiba
df_test = engine.df_pj[
    (engine.df_pj['TIME'] == 'RED BULL BRAGANTINO') &
    (engine.df_pj['ADVERSARIO'] == 'CORITIBA')
].copy()

print(f"Total de jogadores no DataFrame de teste: {len(df_test)}")
print(f"\nPosições:")
print(df_test['POS_REAL'].value_counts())

# Chamar a função
result = engine.get_laterais_aggregated(df_test, window_n=0)

print("\n--- RESULTADO ---")
print(f"LE_DE: {result['LE_DE']}")
print(f"LD_DE: {result['LD_DE']}")

# Verificar manualmente
le_manual = df_test[df_test['POS_REAL'] == 2.6]
ld_manual = df_test[df_test['POS_REAL'] == 2.2]

print("\n--- VERIFICAÇÃO MANUAL ---")
print(f"LE encontrados: {len(le_manual)}")
if len(le_manual) > 0:
    print(le_manual[['NOME', 'POS_REAL', 'DS']])
    print(f"Soma DS: {le_manual['DS'].sum()}")

print(f"\nLD encontrados: {len(ld_manual)}")
if len(ld_manual) > 0:
    print(ld_manual[['NOME', 'POS_REAL', 'DS']])
    print(f"Soma DS: {ld_manual['DS'].sum()}")

# Testar a função is_le e is_ld
print("\n--- TESTE DAS FUNÇÕES is_le e is_ld ---")
for pos in df_test['POS_REAL'].unique():
    if pd.notna(pos):
        is_le_result = abs(float(pos) - 2.6) < 0.01
        is_ld_result = abs(float(pos) - 2.2) < 0.01
        print(f"PosReal {pos}: is_le={is_le_result}, is_ld={is_ld_result}")
