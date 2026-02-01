from src import loader, config
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    data = loader.load_excel_data(file_path)
    df = data["POR_JOGO"]
    print("--- Loader Sucesso ---")
    print(df.head(3).to_string())
    print("\nColunas encontradas:", df.columns.tolist())
    
    # Verificar colunas críticas
    print("\nVerificando colunas críticas:")
    for col in ["BASICA", "DATA", "MANDO", "FF", "FD", "FT"]:
        if col in df.columns:
            print(f"{col}: OK")
        else:
            print(f"{col}: FALTANDO!")
            
    # Verificar valores únicos de POSICAO para saber como filtrar Meias
    if "POSICAO" in df.columns:
        print("\nPosições encontradas:", df["POSICAO"].unique())

except Exception as e:
    print(f"Erro no teste: {e}")
