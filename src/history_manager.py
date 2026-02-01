import pandas as pd
import os
import shutil

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "history")
DATABASE_PATH = os.path.join(HISTORY_DIR, "af_assignments.csv")
LATEST_SNAPSHOT_PATH = os.path.join(HISTORY_DIR, "latest_total_scouts.parquet")

def ensure_history_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def load_af_database():
    """Carrega o histórico de AFs atribuídas a jogos."""
    ensure_history_dir()
    if os.path.exists(DATABASE_PATH):
        return pd.read_csv(DATABASE_PATH)
    return pd.DataFrame(columns=["MATCH_ID", "TIME", "JOGADOR", "AF_VALOR"])

def load_latest_snapshot():
    """Carrega o último total acumulado conhecido."""
    ensure_history_dir()
    if os.path.exists(LATEST_SNAPSHOT_PATH):
        return pd.read_parquet(LATEST_SNAPSHOT_PATH)
    return None

def process_new_upload(df_scouts_new, df_pj_new):
    """
    Processa um novo upload:
    1. Calcula Deltas (Novo Total - Último Snapshot)
    2. Identifica o jogo mais recente de cada time em df_pj_new
    3. Atribui o Delta a esse jogo
    4. Atualiza o banco de dados de AF
    5. Atualiza o Snapshot
    """
    ensure_history_dir()
    
    # Normalizar tabelas (Colunas e Valores)
    df_new = df_scouts_new.copy()
    df_new.columns = [c.upper() for c in df_new.columns] # JOGADOR, TIME, AF
    
    # Padronizar Time e Jogador para buscar match
    df_new["TIME"] = df_new["TIME"].astype(str).str.upper().str.strip()
    df_new["JOGADOR"] = df_new["JOGADOR"].astype(str).str.upper().str.strip()
    
    # Carregar Snapshot Anterior
    df_old = load_latest_snapshot()
    
    # Calcular Deltas
    if df_old is None:
        # Primeiro upload da história
        print("🆕 Primeiro upload detectado. Usando totais absolutos como delta inicial.")
        df_new["AF_DELTA"] = df_new["AF"]
    else:
        print("🔄 Comparando com snapshot anterior...")
        # Normalizar snapshot antigo também
        df_old["TIME"] = df_old["TIME"].astype(str).str.upper().str.strip()
        df_old["JOGADOR"] = df_old["JOGADOR"].astype(str).str.upper().str.strip()
        
        # Merge para calc delta
        merged = pd.merge(
            df_new, 
            df_old[["JOGADOR", "TIME", "AF"]], 
            on=["JOGADOR", "TIME"], 
            how="left", 
            suffixes=("", "_OLD")
        )
        merged["AF_OLD"] = merged["AF_OLD"].fillna(0)
        merged["AF_DELTA"] = merged["AF"] - merged["AF_OLD"]
        df_new = merged
    
    # Filtrar Deltas significativos (diferente de zero)
    deltas = df_new[df_new["AF_DELTA"] != 0][["TIME", "JOGADOR", "AF_DELTA"]].copy()
    
    if deltas.empty:
        print("ℹ️ Nenhuma mudança de AF detectada neste arquivo.")
        return False
    
    # Carregar Database atual
    db_af = load_af_database()
    
    # Identificar ÚLTIMO JOGO de cada time na aba Por Jogo
    # Normalizar df_pj_new
    df_pj_clean = df_pj_new.copy()
    df_pj_clean["TIME"] = df_pj_clean["TIME"].astype(str).str.upper().str.strip()
    
    # Agrupar PJ por Time e pegar a data máxima
    last_games = df_pj_clean.sort_values("DATA").groupby("TIME").tail(1)[["TIME", "MATCH_ID", "DATA"]]
    
    new_assignments = []
    
    # Para cada jogador com Delta, atribuir ao último jogo do seu time
    for _, row in deltas.iterrows():
        time = row["TIME"]
        jogador = row["JOGADOR"]
        valor = row["AF_DELTA"]
        
        # Achar jogo do time
        match_info = last_games[last_games["TIME"] == time]
        
        if not match_info.empty:
            match_id = match_info.iloc[0]["MATCH_ID"]
            new_assignments.append({
                "MATCH_ID": match_id,
                "TIME": time,
                "JOGADOR": jogador,
                "AF_VALOR": valor
            })
        else:
            print(f"⚠️ Sem jogo encontrado para time {time} (Jogador: {jogador}). Delta ignorado.")
            
    if not new_assignments:
        print("⚠️ Nenhum jogo compatível encontrado para atribuir os deltas.")
        return False
        
    df_assignments = pd.DataFrame(new_assignments)
    
    # Atualizar Database
    # Remover duplicatas? Se rodarmos o mesmo arquivo 2x, vai duplicar?
    # Risco: O usuário sobe o arquivo, calcula delta. Sobe DE NOVO o mesmo arquivo.
    # O snapshot já foi atualizado na 1ª vez. Então na 2ª, o Delta será 0.
    # Então é SEGURO! O snapshot previne duplicação do mesmo upload.
    
    # Concatenar e Salvar DB
    db_updated = pd.concat([db_af, df_assignments], ignore_index=True)
    db_updated.to_csv(DATABASE_PATH, index=False)
    
    # Atualizar Snapshot (Salva o estado ATUAL como o novo 'Antigo')
    df_new[["JOGADOR", "TIME", "AF"]].to_parquet(LATEST_SNAPSHOT_PATH, index=False)
    
    print(f"✅ Processamento concluído. {len(new_assignments)} registros de AF adicionados.")
    return True

def reset_history():
    """Limpa todo o histórico (CUIDADO!)."""
    if os.path.exists(HISTORY_DIR):
        shutil.rmtree(HISTORY_DIR)
        ensure_history_dir()
