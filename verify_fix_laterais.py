import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
print("=== VERIFICAÇÃO PÓS-CORREÇÃO LATERAIS ===\n")

engine = CartolaEngine(file_path)
mandante = "CRUZEIRO"
visitante = "CORITIBA"

# Filtro TODAS, N=1
result = engine.generate_laterais_table(mandante, visitante, window_n=1, mando_mode="TODOS")

print(f"Mandante: {result['MANDANTE']}")
print(f"Visitante: {result['VISITANTE']}")

print("\n--- LADO ESQUERDO (MANDANTE) ---")
print(f"COC_LE_DE (Cruzeiro): {result['COC_LE_DE']} (Esperado: 0)")
print(f"CDF_LE_DE (Visitante->Adv): {result['CDF_LE_DE']} (Esperado: 0 - RBR)")

print("\n--- LADO DIREITO (VISITANTE) ---")
print(f"COF_LD_DE (Coritiba): {result['COF_LD_DE']} (Esperado: 3)")
print(f"CDC_LD_DE (Mandante->Adv): {result['CDC_LD_DE']} (Esperado: 2 - Botafogo)")

success = True
if result['CDF_LE_DE'] != 0.0: success = False
if result['CDC_LD_DE'] != 2.0: success = False

if success:
    print("\n✅ SUCESSO! A lógica está correta.")
else:
    print("\n❌ FALHA! Os valores não batem.")
