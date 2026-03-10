import pandas as pd
import os
import shutil
import json

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "history")
DATABASE_PATH = os.path.join(HISTORY_DIR, "af_assignments.csv")
LATEST_SNAPSHOT_PATH = os.path.join(HISTORY_DIR, "latest_total_scouts.parquet")
KNOWN_MATCHES_PATH = os.path.join(HISTORY_DIR, "known_matches.json")

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

def load_known_matches():
    """Carrega a lista de jogos já conhecidos pelo sistema."""
    ensure_history_dir()
    if os.path.exists(KNOWN_MATCHES_PATH):
        with open(KNOWN_MATCHES_PATH, "r") as f:
            return set(json.load(f))
    return set()

def save_known_matches(matches_set):
    """Salva a lista de jogos conhecidos."""
    ensure_history_dir()
    with open(KNOWN_MATCHES_PATH, "w") as f:
        json.dump(sorted(list(matches_set)), f, indent=2)

def _get_player_matches(df_pj, jogador, time):
    """
    Retorna a lista de MATCH_IDs em que um jogador específico participou.
    Busca por NOME + TIME na aba Por Jogo.
    """
    mask = (df_pj["NOME"] == jogador) & (df_pj["TIME"] == time)
    return set(df_pj[mask]["MATCH_ID"].unique())

def _get_team_matches_from_matchids(match_ids, team):
    """
    Filtra MATCH_IDs que envolvem um time específico.
    MATCH_ID formato: DATA|MANDANTE|VISITANTE
    """
    team_matches = set()
    for m in match_ids:
        parts = m.split("|")
        if len(parts) == 3 and team in [parts[1], parts[2]]:
            team_matches.add(m)
    return team_matches

def _get_team_matches_without_af(all_known_matches, db_af, team):
    """
    Retorna jogos CONHECIDOS do time que NÃO têm nenhuma entrada de AF no banco.
    Esses são jogos 'órfãos' - registrados como conhecidos mas sem AF atribuída.
    """
    team_known = _get_team_matches_from_matchids(all_known_matches, team)
    
    if db_af.empty:
        return team_known
    
    team_db_matches = set(db_af[db_af["TIME"] == team]["MATCH_ID"].unique())
    return team_known - team_db_matches

def process_new_upload(df_scouts_new, df_pj_new):
    """
    Processa um novo upload com lógica robusta:
    
    FLUXO PRINCIPAL:
    1. Identifica JOGOS NOVOS comparando com a lista de jogos conhecidos
    2. Calcula Deltas de AF (Novo Total - Último Snapshot)
    3. Para cada jogador com delta, identifica em quais jogos NOVOS ele participou
    4. Se participou em 1 jogo novo -> atribui delta inteiro (caso padrão, 99%)
    5. Se participou em 2+ jogos novos -> divide igualmente (caso raríssimo)
    
    BLINDAGENS:
    - Transferências: jogadores que saíram do time têm AF fantasma removida
    - Deltas negativos: ignorados com aviso (indicam erro de dados ou transferência)
    - Deltas órfãos: quando há delta mas nenhum jogo novo, busca o jogo mais recente
      do time que ainda não tem AF no banco (resolve o caso de planilha com AF atrasada)
    
    Returns:
        str: Mensagem de status do processamento
    """
    ensure_history_dir()
    
    # =========================================================================
    # ETAPA 1: Normalizar dados de entrada
    # =========================================================================
    df_new = df_scouts_new.copy()
    df_new.columns = [c.upper() for c in df_new.columns]
    df_new["TIME"] = df_new["TIME"].astype(str).str.upper().str.strip()
    df_new["JOGADOR"] = df_new["JOGADOR"].astype(str).str.upper().str.strip()
    
    # Normalizar PJ (já vem normalizado do engine, mas garantir)
    df_pj = df_pj_new.copy()
    df_pj["NOME"] = df_pj["NOME"].astype(str).str.upper().str.strip()
    df_pj["TIME"] = df_pj["TIME"].astype(str).str.upper().str.strip()
    
    # =========================================================================
    # ETAPA 2: Identificar JOGOS NOVOS
    # =========================================================================
    current_matches = set(df_pj["MATCH_ID"].unique())
    known_matches = load_known_matches()
    new_matches = current_matches - known_matches
    
    # =========================================================================
    # ETAPA 3: Carregar snapshot anterior e calcular deltas
    # =========================================================================
    df_old = load_latest_snapshot()
    
    if df_old is None:
        # Primeiro upload da história
        print(f"🆕 Primeiro upload detectado. {len(current_matches)} jogos, {len(df_new)} jogadores.")
        df_new["AF_DELTA"] = df_new["AF"]
    else:
        print("🔄 Comparando com snapshot anterior...")
        df_old["TIME"] = df_old["TIME"].astype(str).str.upper().str.strip()
        df_old["JOGADOR"] = df_old["JOGADOR"].astype(str).str.upper().str.strip()
        
        # Merge para calcular delta
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
        
        # =====================================================================
        # BLINDAGEM: Detectar jogadores que SAÍRAM do time (transferências)
        # =====================================================================
        old_keys = set(zip(df_old["JOGADOR"], df_old["TIME"]))
        new_keys = set(zip(df_new["JOGADOR"], df_new["TIME"]))
        transferred = old_keys - new_keys
        
        if transferred:
            print(f"⚠️ {len(transferred)} jogador(es) transferido(s)/removido(s) detectado(s):")
            
            db_af = load_af_database()
            
            if not db_af.empty:
                rows_before = len(db_af)
                for jogador, time in transferred:
                    print(f"   🔄 {jogador} ({time})")
                    mask = (db_af["JOGADOR"].str.upper().str.strip() == jogador) & \
                           (db_af["TIME"].str.upper().str.strip() == time)
                    db_af = db_af[~mask]
                
                rows_removed = rows_before - len(db_af)
                if rows_removed > 0:
                    print(f"   🗑️ {rows_removed} registro(s) de AF fantasma removido(s).")
                    db_af.to_csv(DATABASE_PATH, index=False)
    
    # =========================================================================
    # ETAPA 4: Filtrar deltas significativos
    # =========================================================================
    deltas = df_new[df_new["AF_DELTA"] != 0][["TIME", "JOGADOR", "AF_DELTA"]].copy()
    
    has_new_matches = len(new_matches) > 0
    has_deltas = not deltas.empty
    
    if not has_new_matches and not has_deltas:
        print("ℹ️ Nenhum jogo novo e nenhuma mudança de AF.")
        df_new[["JOGADOR", "TIME", "AF"]].to_parquet(LATEST_SNAPSHOT_PATH, index=False)
        save_known_matches(current_matches)
        return "Nenhuma alteração detectada. Snapshot atualizado."
    
    if has_new_matches:
        print(f"🆕 {len(new_matches)} jogo(s) novo(s):")
        for m in sorted(new_matches):
            print(f"   📋 {m}")
    
    if has_deltas:
        print(f"📊 {len(deltas)} jogador(es) com mudança de AF.")
    else:
        print("ℹ️ Jogos novos detectados, mas nenhuma mudança de AF.")
        df_new[["JOGADOR", "TIME", "AF"]].to_parquet(LATEST_SNAPSHOT_PATH, index=False)
        save_known_matches(current_matches)
        return f"{len(new_matches)} jogo(s) novo(s) registrado(s), sem mudança de AF."
    
    # =========================================================================
    # ETAPA 5: Atribuir delta aos jogos CORRETOS
    # =========================================================================
    db_af = load_af_database()
    
    # Atualizar known_matches ANTES de buscar órfãos (inclui novos jogos)
    all_known_after = known_matches | current_matches
    
    new_assignments = []
    warnings = []
    
    for _, row in deltas.iterrows():
        time = row["TIME"]
        jogador = row["JOGADOR"]
        delta = row["AF_DELTA"]
        
        if delta < 0:
            warnings.append(f"⚠️ Delta negativo ignorado: {jogador} ({time}) delta={delta}")
            continue
        
        # ---- PASSO A: Encontrar jogos NOVOS em que este jogador participou ----
        player_all_matches = _get_player_matches(df_pj, jogador, time)
        player_new_matches = player_all_matches & new_matches
        
        if player_new_matches:
            # Caso padrão: jogador participou de jogo(s) novo(s)
            if len(player_new_matches) == 1:
                match_id = list(player_new_matches)[0]
                new_assignments.append({
                    "MATCH_ID": match_id,
                    "TIME": time,
                    "JOGADOR": jogador,
                    "AF_VALOR": delta
                })
            else:
                # Caso raro: 2+ jogos novos -> dividir igualmente
                n_games = len(player_new_matches)
                af_per_game = delta / n_games
                warnings.append(
                    f"⚠️ {jogador} ({time}): delta={delta} dividido entre {n_games} jogos "
                    f"({af_per_game:.1f}/jogo)"
                )
                for match_id in sorted(player_new_matches):
                    new_assignments.append({
                        "MATCH_ID": match_id,
                        "TIME": time,
                        "JOGADOR": jogador,
                        "AF_VALOR": round(af_per_game, 1)
                    })
            continue
        
        # ---- PASSO B: Nenhum jogo novo -> buscar jogo ÓRFÃO (sem AF no banco) ----
        # Isso acontece quando a planilha anterior tinha AF desatualizada
        # O jogo já foi registrado como "conhecido" mas nunca recebeu AF
        orphan_matches = _get_team_matches_without_af(all_known_after, db_af, time)
        
        # Filtrar apenas jogos em que o jogador participou
        player_orphan_matches = player_all_matches & orphan_matches
        
        if player_orphan_matches:
            # Atribuir ao jogo órfão mais recente
            if len(player_orphan_matches) == 1:
                match_id = list(player_orphan_matches)[0]
                new_assignments.append({
                    "MATCH_ID": match_id,
                    "TIME": time,
                    "JOGADOR": jogador,
                    "AF_VALOR": delta
                })
                warnings.append(
                    f"ℹ️ {jogador} ({time}): delta={delta} atribuído a jogo órfão {match_id}"
                )
            else:
                n_games = len(player_orphan_matches)
                af_per_game = delta / n_games
                warnings.append(
                    f"⚠️ {jogador} ({time}): delta={delta} dividido entre {n_games} jogos órfãos "
                    f"({af_per_game:.1f}/jogo)"
                )
                for match_id in sorted(player_orphan_matches):
                    new_assignments.append({
                        "MATCH_ID": match_id,
                        "TIME": time,
                        "JOGADOR": jogador,
                        "AF_VALOR": round(af_per_game, 1)
                    })
            continue
        
        # ---- PASSO C: Fallback - buscar qualquer jogo novo do TIME ----
        # Jogador tem delta mas não aparece em nenhum jogo (novo ou órfão)
        # Pode ser jogador que entrou no elenco mas não jogou
        team_new_matches = _get_team_matches_from_matchids(new_matches, time)
        
        if team_new_matches:
            latest_match = sorted(team_new_matches)[-1]
            new_assignments.append({
                "MATCH_ID": latest_match,
                "TIME": time,
                "JOGADOR": jogador,
                "AF_VALOR": delta
            })
            warnings.append(
                f"ℹ️ {jogador} ({time}): delta={delta} atribuído ao jogo mais recente do time "
                f"{latest_match} (jogador não encontrado na aba PJ)"
            )
            continue
        
        # ---- PASSO D: Fallback final - buscar qualquer jogo órfão do TIME ----
        team_orphan_matches = _get_team_matches_without_af(all_known_after, db_af, time)
        
        if team_orphan_matches:
            latest_orphan = sorted(team_orphan_matches)[-1]
            new_assignments.append({
                "MATCH_ID": latest_orphan,
                "TIME": time,
                "JOGADOR": jogador,
                "AF_VALOR": delta
            })
            warnings.append(
                f"ℹ️ {jogador} ({time}): delta={delta} atribuído ao jogo órfão do time "
                f"{latest_orphan} (jogador não encontrado na aba PJ)"
            )
            continue
        
        # ---- PASSO E: Último recurso - atribuir ao jogo mais recente do time ----
        # Isso acontece quando o Gato Mestre atualiza AF retroativamente
        # (ex: jogador ganhou AF em jogo de copa, ou correção de dados)
        # O time não tem jogo novo NEM jogo órfão, mas o delta é real.
        # Atribuir ao jogo mais recente do time (mesmo que já tenha AF).
        all_team_matches = _get_team_matches_from_matchids(all_known_after, time)
        
        if all_team_matches:
            latest_match = sorted(all_team_matches)[-1]
            new_assignments.append({
                "MATCH_ID": latest_match,
                "TIME": time,
                "JOGADOR": jogador,
                "AF_VALOR": delta
            })
            warnings.append(
                f"⚠️ {jogador} ({time}): delta={delta} atribuído ao jogo mais recente "
                f"{latest_match} (AF retroativa - sem jogo novo disponível)"
            )
        else:
            warnings.append(
                f"❌ {jogador} ({time}): delta={delta} PERDIDO - nenhum jogo disponível!"
            )
    
    # Imprimir avisos
    for w in warnings:
        print(w)
    
    # =========================================================================
    # ETAPA 6: Salvar tudo
    # =========================================================================
    if new_assignments:
        df_assignments = pd.DataFrame(new_assignments)
        
        # Concatenar com banco existente
        db_updated = pd.concat([db_af, df_assignments], ignore_index=True)
        db_updated.to_csv(DATABASE_PATH, index=False)
        print(f"✅ {len(new_assignments)} registro(s) de AF adicionado(s) ao banco.")
    
    # Atualizar Snapshot
    df_new[["JOGADOR", "TIME", "AF"]].to_parquet(LATEST_SNAPSHOT_PATH, index=False)
    
    # Atualizar lista de jogos conhecidos
    save_known_matches(current_matches)
    
    msg = f"Histórico atualizado! {len(new_assignments)} registros de AF em {len(new_matches)} jogo(s) novo(s)."
    if warnings:
        msg += f" ({len(warnings)} aviso(s))"
    
    print(f"✅ {msg}")
    return msg

def reset_history():
    """Limpa todo o histórico (CUIDADO!)."""
    if os.path.exists(HISTORY_DIR):
        shutil.rmtree(HISTORY_DIR)
        ensure_history_dir()
    print("🗑️ Histórico completamente resetado.")
