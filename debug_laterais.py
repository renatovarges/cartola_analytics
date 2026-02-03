
from src.engine import CartolaEngine
import pandas as pd
import numpy as np

INPUT_FILE = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    engine = CartolaEngine(INPUT_FILE)
    df = engine.df_pj
    
    print("--- DEBUG POS_REAL ---")
    if "POS_REAL" in df.columns:
        print("Tipo da coluna:", df["POS_REAL"].dtype)
        print("Valores únicos:", df["POS_REAL"].unique())
        print("Amostra nula:", df["POS_REAL"].isna().sum())
        
        # Teste filtro
        le_count = df[df["POS_REAL"].astype(str).str.contains("2.6", na=False)].shape[0]
        ld_count = df[df["POS_REAL"].astype(str).str.contains("2.2", na=False)].shape[0]
        print(f"Contagem LE (string '2.6'): {le_count}")
    print("--- DEBUG JOGOS DISPONÍVEIS ---")
    if "MATCH_ID" in df.columns:
        print(df["MATCH_ID"].unique())
        
    print("-------------------------------")

except Exception as e:
    print(f"Erro: {e}")
