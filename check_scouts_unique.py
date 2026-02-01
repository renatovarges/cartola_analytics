from src import loader
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
SHEET_SCOUTS = "Scouts"

try:
    df = pd.read_excel(file_path, sheet_name=SHEET_SCOUTS)
    n_rows = len(df)
    n_unique = df["Jogador"].nunique()
    
    print(f"Linhas Totais: {n_rows}")
    print(f"Jogadores Únicos: {n_unique}")
    
    if n_rows == n_unique:
        print("CONCLUSÃO: 1 linha por jogador (Tabela Sumarizada).")
    else:
        print("CONCLUSÃO: Múltiplas linhas por jogador (Histórico disponível).")

except Exception as e:
    print(f"Erro: {e}")
