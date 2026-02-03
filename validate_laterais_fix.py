import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== VALIDAÇÃO PÓS-CORREÇÃO ===\n")

engine = CartolaEngine(file_path)

# Testar jogo Coritiba x RB Bragantino
result = engine.generate_laterais_table("CORITIBA", "RED BULL BRAGANTINO", window_n=5, mando_mode="POR_MANDO")

print("Jogo: CORITIBA x RED BULL BRAGANTINO\n")
print("--- LATERAL ESQUERDO (Cedidos pelo Coritiba) ---")
print(f"CDF_LE_DE (Desarmes): {result['CDF_LE_DE']} ← Deve ser 0")
print(f"CDF_LE_PG (G+A): {result['CDF_LE_PG']}")
print(f"CDF_LE_BAS (Média Básica): {result['CDF_LE_BAS']:.1f}")

print("\n--- LATERAL DIREITO (Cedidos pelo Coritiba) ---")
print(f"CDF_LD_DE (Desarmes): {result['CDF_LD_DE']} ← Deve ser 0")
print(f"CDF_LD_PG (G+A): {result['CDF_LD_PG']}")
print(f"CDF_LD_BAS (Média Básica): {result['CDF_LD_BAS']:.1f}")

print("\n--- DataFrame para Streamlit ---")
df = pd.DataFrame([result])
print(f"Colunas disponíveis: {df.columns.tolist()}")
print(f"\nValor de CDF_LE_DE no DataFrame: {df['CDF_LE_DE'].iloc[0]}")

# Verificar se as colunas do app.py existem
colunas_app = [
    "COC_LE_DE", "CDF_LE_DE", "COC_LE_PG", "CDF_LE_PG", "COC_LE_BAS", "CDF_LE_BAS",
    "COC_LD_DE", "CDF_LD_DE", "COC_LD_PG", "CDF_LD_PG", "COC_LD_BAS", "CDF_LD_BAS",
    "COC_SG", "CDF_SG"
]

print("\n--- Verificação de Colunas ---")
for col in colunas_app:
    if col in df.columns:
        print(f"✓ {col}: {df[col].iloc[0]}")
    else:
        print(f"✗ {col}: AUSENTE!")
