
import pandas as pd
# from src.config import INPUT_FILE
INPUT_FILE = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    xls = pd.ExcelFile(INPUT_FILE)
    print(f"ABAS ENCONTRADAS: {xls.sheet_names}")
    
    target_sheet = None
    for s in xls.sheet_names:
        if "POR JOGO" in s.upper():
            target_sheet = s
            break
            
    if target_sheet:
        print(f"Lendo aba '{target_sheet}'...")
        df = pd.read_excel(INPUT_FILE, sheet_name=target_sheet)
        print("COLUNAS:")
        print(list(df.columns))
    else:
        print("Nenhuma aba 'Por Jogo' encontrada.")

except Exception as e:
    print(e)
