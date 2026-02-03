import pandas as pd
import os
import sys
from . import config

def normalize_text(text):
    """Remove espaços extras e converte para maiúsculas."""
    if pd.isna(text):
        return ""
    return str(text).strip().upper()

def find_column(df, candidates):
    """Procura uma coluna no DataFrame baseada em uma lista de candidatos."""
    df_cols_upper = {c.upper().strip(): c for c in df.columns}
    for cand in candidates:
        cand_upper = cand.upper().strip()
        if cand_upper in df_cols_upper:
            return df_cols_upper[cand_upper]
    return None

def load_excel_data(file_path):
    """
    Carrega o arquivo Excel e retorna um dicionário com os DataFrames prontos.
    Lê a aba 'Por Jogo' (Primária) e 'Scouts' (Secundária).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    print(f"Carregando dados de: {file_path}")
    xls = pd.ExcelFile(file_path)
    
    datasets = {}
    
    # --- Carregar ABA "Por Jogo" ---
    # Tenta encontrar o nome correto da aba (case insensitive)
    sheet_pj = None
    for s in xls.sheet_names:
        if config.SHEET_POR_JOGO.upper() in s.upper():
            sheet_pj = s
            break
            
    if sheet_pj:
        print(f"Lendo aba '{sheet_pj}'...")
        df_pj = pd.read_excel(file_path, sheet_name=sheet_pj)
        
        # Renomear colunas para o padrão interno
        rename_map = {}
        found_cols = []
        for key, candidates in config.COLS_POR_JOGO.items():
            original_col = find_column(df_pj, candidates)
            if original_col:
                rename_map[original_col] = key
                found_cols.append(key)
        
        df_pj = df_pj.rename(columns=rename_map)
        
        # Converter DATA
        if "DATA" in df_pj.columns:
            df_pj["DATA"] = pd.to_datetime(df_pj["DATA"], errors="coerce", dayfirst=True)
            
        # Normalizar TEXTOS
        for txt_col in ["NOME", "TIME", "ADVERSARIO", "MANDO", "POSICAO"]:
            if txt_col in df_pj.columns:
                df_pj[txt_col] = df_pj[txt_col].apply(normalize_text)
                
        # Normalizar MANDO (CASA/FORA)
        # Se vier C/F ou HOME/AWAY, padronizar para CASA/FORA
        if "MANDO" in df_pj.columns:
            def fix_mando(val):
                if val in ["C", "CASA", "HOME"]: return "CASA"
                if val in ["F", "FORA", "AWAY", "VISITANTE"]: return "FORA"
                return val
            df_pj["MANDO"] = df_pj["MANDO"].apply(fix_mando)
            
        # Preencher numéricos vazios com 0
        num_cols = ["G", "A", "FF", "FD", "FT", "BASICA", "PONTOS", "DS", "SG", "DE", "DP", "GS", "POS_REAL"]
        for nc in num_cols:
            if nc in df_pj.columns:
                df_pj[nc] = pd.to_numeric(df_pj[nc], errors="coerce").fillna(0)
                
        datasets["POR_JOGO"] = df_pj
        print(f"Aba 'Por Jogo' carregada com {len(df_pj)} linhas. Colunas mapeadas: {found_cols}")
    else:
        print(f"ERRO: Aba '{config.SHEET_POR_JOGO}' não encontrada no Excel.")
        
    # --- Carregar ABA "Scouts" (Secundária) ---
    sheet_scouts = None
    for s in xls.sheet_names:
        if config.SHEET_SCOUTS.upper() in s.upper():
            sheet_scouts = s
            break
            
    if sheet_scouts:
        print(f"Lendo aba '{sheet_scouts}'...")
        df_sc = pd.read_excel(file_path, sheet_name=sheet_scouts)
        # Por enquanto lemos bruta, sem normalização pesada, pois será uso secundário
        datasets["SCOUTS"] = df_sc
    
    return datasets
