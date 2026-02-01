from src import loader
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
SHEET_SCOUTS = "Scouts"

try:
    print(f"Lendo aba '{SHEET_SCOUTS}' de {file_path}...")
    df = pd.read_excel(file_path, sheet_name=SHEET_SCOUTS, nrows=20) # Ler poucas linhas para ver estrutura
    
    print("\n--- Colunas ---")
    print(df.columns.tolist())
    
    print("\n--- Head ---")
    print(df.head(10).to_string())
    
    # Verificar se coluna AF existe
    af_cols = [c for c in df.columns if "AF" in c.upper()]
    print(f"\nColunas de AF encontradas: {af_cols}")

except Exception as e:
    print(f"Erro: {e}")
