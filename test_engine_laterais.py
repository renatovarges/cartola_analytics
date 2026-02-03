import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.engine import CartolaEngine

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"

print("=== TESTE REAL DO ENGINE ===\n")

# Inicializar engine
engine = CartolaEngine(file_path)

# Gerar tabela para o jogo Coritiba x RB Bragantino
result = engine.generate_laterais_table("CORITIBA", "RED BULL BRAGANTINO", window_n=5, mando_mode="POR_MANDO")

print("Resultado do Engine:")
print(f"CDF_LE_DE (Desarmes cedidos LE): {result['CDF_LE_DE']}")
print(f"CDF_LD_DE (Desarmes cedidos LD): {result['CDF_LD_DE']}")

print("\n--- Todos os valores ---")
for key, value in result.items():
    if 'CDF' in key or 'CDC' in key:
        print(f"{key}: {value}")
