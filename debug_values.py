
from src.engine import CartolaEngine
import pandas as pd

INPUT_FILE = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    engine = CartolaEngine(INPUT_FILE)
    df = engine.df_pj
    
    print("--- DEBUG DE VALUES ---")
    # Filtro LE e LD
    mask_le = df["POS_REAL"].astype(str).str.contains("2.6", na=False)
    mask_ld = df["POS_REAL"].astype(str).str.contains("2.2", na=False)
    
    df_le = df[mask_le]
    df_ld = df[mask_ld]
    
    print(f"Total LE: {len(df_le)}")
    print(f"Total LD: {len(df_ld)}")
    
    print("\nAmostra LE (Nome, DE, DS, G, A):")
    cols = ["NOME", "DE", "DS", "G", "A", "BASICA"]
    print(df_le[cols].head(10).to_string())
    
    print("\nAmostra LD (Nome, DE, DS, G, A):")
    print(df_ld[cols].head(10).to_string())
    
    print("\nSoma Total DE LE:", df_le["DE"].sum())
    print("Soma Total DS LE:", df_le["DS"].sum())
    print("Soma Total DE LD:", df_ld["DE"].sum())
    print("Soma Total DS LD:", df_ld["DS"].sum())

except Exception as e:
    print(f"Erro: {e}")
