import pandas as pd
import sys
import os

# Ajustar path para importar módulos src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.loader import load_excel_data
from src.history_manager import process_new_upload, reset_history
from src.engine import CartolaEngine

print("="*50)
print("DIAGNÓSTICO DE AF")
print("="*50)

# 1. Carregar Engine e Dados
file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
print(f"Carregando arquivo: {file_path}")

try:
    datasets = load_excel_data(file_path)
    df_scouts = datasets.get("SCOUTS")
    df_pj = datasets.get("POR_JOGO")
    
    print(f"\n[SCOUTS] Shape: {df_scouts.shape}")
    print(f"[SCOUTS] Colunas: {list(df_scouts.columns)}")
    
    if "AF" in df_scouts.columns:
        total_af = df_scouts["AF"].sum()
        print(f"[SCOUTS] Soma Total AF: {total_af}")
        print(f"[SCOUTS] Jogadores com AF > 0: {len(df_scouts[df_scouts['AF'] > 0])}")
    else:
        print("❌ ERRO: Coluna AF não encontrada em SCOUTS!")

    print(f"\n[POR JOGO] Shape: {df_pj.shape}")
    
    # Simular processamento (MOCK)
    # Criar engine para ter MATCH_ID
    engine = CartolaEngine(file_path)
    df_pj_com_match = engine.df_pj
    
    print("\n[ENGINE] MATCH_IDs gerados. Exemplo:")
    print(df_pj_com_match[["DATA", "TIME", "ADVERSARIO", "MATCH_ID"]].head(3))
    
    print("\n--- TENTANDO PROCESSAR NOVO UPLOAD ---")
    result = process_new_upload(df_scouts, df_pj_com_match)
    print(f"\nResultado process_new_upload: {result}")

except Exception as e:
    print(f"\n❌ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
