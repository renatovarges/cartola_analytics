import pandas as pd
import numpy as np
import unicodedata
from . import config, loader
from .classificacao import load_meias_volantes_classification
from .history_manager import load_af_database, process_new_upload, reset_history

class CartolaEngine:
    def __init__(self, file_path):
        self.datasets = loader.load_excel_data(file_path)
        self.df_pj = self.datasets["POR_JOGO"]
        self.df_scouts = self.datasets.get("SCOUTS") # Dados acumulados
        
        # Carregar classificação Meias vs Volantes
        self.classificacao_mv = load_meias_volantes_classification()
        
        # Pré-cálculos globais (Match IDs, etc)
        self._prepare_base_data()
        
    def _prepare_base_data(self):
        """Cria identificadores de partida e normaliza dados para cruzamento."""
        df = self.df_pj.copy()
        
        # Criar Match ID único: DATA_MANDANTE_VISITANTE
        def get_match_signature(row):
            if row["MANDO"] == "CASA":
                home = row["TIME"]
                away = row["ADVERSARIO"]
            else:
                home = row["ADVERSARIO"]
                away = row["TIME"]
            d_str = row["DATA"].strftime("%Y-%m-%d") if pd.notna(row["DATA"]) else "0000-00-00"
            return f"{d_str}|{home}|{away}"
        
        df["MATCH_ID"] = df.apply(get_match_signature, axis=1)
        self.df_pj = df

    def process_af_update(self):
        """
        Acionado manualmente para processar o arquivo carregado como uma NOVA ATUALIZAÇÃO.
        Calcula deltas e salva no banco de dados de histórico.
        """
        if self.df_scouts is None:
            return "Aba SCOUTS não encontrada."
            
        print("🔄 Iniciando atualização de histórico AF...")
        # Processa upload usando df_pj atual (com Match IDs)
        return process_new_upload(self.df_scouts, self.df_pj)

    def get_meias_stats_raw(self, date_cutoff=None, mv_filter=None):
        """
        Gera métricas, injetando AF do histórico persistente.
        """
        # 1. Filtro de Posição
        # 1. Filtro de Posição
        if mv_filter == "ATACANTE":
             target_ids = config.POS_IDS["ATACANTE"]
        else:
             target_ids = config.POS_IDS["MEIA_ONLY"]
             
        df = self.df_pj[self.df_pj["POSICAO"].astype(str).isin(target_ids)].copy()
        
        # 2. Carregar e Merge AF do Banco de Dados
        df_af_db = load_af_database()
        
        if not df_af_db.empty:
            # Normalizar para merge
            df["NOME_UPPER"] = df["NOME"].str.upper()
            df["TIME_UPPER"] = df["TIME"].str.upper()
            
            df_af_db["JOGADOR"] = df_af_db["JOGADOR"].str.upper()
            df_af_db["TIME"] = df_af_db["TIME"].str.upper()
            
            # Preparar DB renomeando para evitar colisão
            db_to_merge = df_af_db[["MATCH_ID", "TIME", "JOGADOR", "AF_VALOR"]].rename(
                columns={"TIME": "TIME_DB", "JOGADOR": "JOGADOR_DB"}
            )
            
            # Merge seguro
            df = pd.merge(
                df,
                db_to_merge,
                left_on=["MATCH_ID", "TIME_UPPER", "NOME_UPPER"],
                right_on=["MATCH_ID", "TIME_DB", "JOGADOR_DB"],
                how="left"
            )
            # Preencher NaN com 0
            df["AF"] = df["AF_VALOR"].fillna(0.0)
            
            # Limpar colunas auxiliares
            df = df.drop(columns=["TIME_DB", "JOGADOR_DB", "AF_VALOR", "NOME_UPPER", "TIME_UPPER", "CLASSIFICACAO_MV"], errors="ignore")  
        else:
            df["AF"] = 0.0

        # 3. Filtro Meia vs Volante
        if mv_filter and self.classificacao_mv:
            def _classify(nome):
                nome_upper = str(nome).strip().upper()
                # Tentar match direto primeiro
                result = self.classificacao_mv.get(nome_upper)
                if result:
                    return result
                # Fallback: tentar sem acentos
                nfkd = unicodedata.normalize('NFKD', nome_upper)
                nome_norm = ''.join(c for c in nfkd if not unicodedata.combining(c))
                return self.classificacao_mv.get(nome_norm)
            
            df["CLASSIFICACAO_MV"] = df["NOME"].apply(_classify)
            if mv_filter == "MEIA":
                df = df[df["CLASSIFICACAO_MV"] == "MEIA"]
            elif mv_filter == "VOLANTE":
                df = df[df["CLASSIFICACAO_MV"] == "VOLANTE"]
        
        # 4. Filtro de Data
        if date_cutoff:
             df = df[df["DATA"] < pd.to_datetime(date_cutoff)]
             
        # 5. Cálculos de Métricas
        df["PG"] = df["G"] + df["A"]
        
        # CHUTES: Soma FF+FD+FT
        # Verificar se as colunas existem (caso o input seja diferente)
        for col in ["FF", "FD", "FT"]:
             if col not in df.columns: df[col] = 0
             
        df["CHUTES"] = df["FF"] + df["FD"] + df["FT"]
        df["DE"] = df["DS"] if "DS" in df.columns else 0
        
        if "BASICA" not in df.columns:
             df["BASICA"] = df["PONTOS"]
        
        return df

    def get_aggregated_stats(self, df_raw, window_n, time_filter=None, mando_filter=None):
        """
        Calcula média dos últimos N jogos para um time num contexto específico.
        Ex: Flamengo, Mando='CASA' -> Retorna média de PG, CHUTES, BASICA.
        """
        df = df_raw.copy()
        
        # Filtro de Time
        if time_filter:
            df = df[df["TIME"] == time_filter]
            
        # Filtro de Mando
        if mando_filter == "CASA":
            df = df[df["MANDO"] == "CASA"]
        elif mando_filter == "FORA":
            df = df[df["MANDO"] == "FORA"]
            
        # Ordenar e Janela
        df = df.sort_values("DATA", ascending=True)
        
        # Agrupa POR JOGO (pois pode ter múltiplos meias no mesmo jogo)
        # Queremos saber: "Nesse jogo, o time gerou X de volume de meia"
        # O documento diz: "Soma das AF dentro da janela", "Média Básica considera jogos dentro da janela"
        
        # Agregação Nível JOGO (Soma de todos os meias do time na partida)
        # BASICA é média ou soma? Documento: "MÉDIA BÁSICA – Média".
        # Geralmente soma-se a pontuação dos meias, mas se pede Média, é Média dos jogadores?
        # Interpretacao: Média do Time por Jogo? Ou Média per Capita?
        # Geralmente em analise de time: "O Meio campo do Fla gera 15pts de basica por jogo". (SOMA)
        # Mas o nome é "Média Básica".
        # Vou usar SOMA dos scouts de volume (G, A, Chutes) e MÉDIA da Básica (per capita).
        
        game_stats = df.groupby("MATCH_ID").agg({
            "G": "sum",
            "A": "sum",
            "PG": "sum",
            "CHUTES": "sum",
            "AF": "sum",
            "DE": "sum",
            "BASICA": "mean", # Média dos meias que jogaram
            "DATA": "first"
        }).sort_values("DATA")
        
        # Aplicar Janela (últimos N jogos do TIME)
        if hasattr(game_stats, "tail"):
             # Se for 0 pega tudo
            slice_stats = game_stats.tail(window_n) if window_n > 0 else game_stats
        else:
            slice_stats = game_stats
            
        if len(slice_stats) == 0:
            return {k: 0 for k in ["G", "A", "PG", "CHUTES", "AF", "DE", "BASICA"]}
            
        return {
            "G": slice_stats["G"].sum(),
            "A": slice_stats["A"].sum(),
            "PG": slice_stats["PG"].sum(), # Soma na janela! (Documento: 'Método: SOMA')
            "CHUTES": slice_stats["CHUTES"].sum(), # SOMA
            "AF": slice_stats["AF"].sum(), # SOMA
            "DE": slice_stats["DE"].sum(), # SOMA
            "BASICA": slice_stats["BASICA"].mean() # MÉDIA na janela
        }

    def generate_confronto_table(self, mandante, visitante, window_n=5, date_cutoff=None, mando_mode="POR_MANDO", rodada_curr=None, mv_filter=None):
        """
        Gera a linha da tabela final para um confronto específico.
        
        Args:
            mandante: Nome do time mandante
            visitante: Nome do time visitante  
            window_n: Janela de jogos
            date_cutoff: Data limite
            mando_mode: "POR_MANDO" ou "TODOS"
            rodada_curr: Número da rodada
            mv_filter: "MEIA", "VOLANTE" ou None
        """
        # Normalizar nomes dos times usando aliases
        def normalize_team_name(team):
            """Aplica aliases de times para normalizar nomes."""
            if team in config.TEAM_ALIASES:
                return config.TEAM_ALIASES[team]
            return team
        
        mandante = normalize_team_name(mandante)
        visitante = normalize_team_name(visitante)
        
        # --- AUTO-CUTOFF (Regra de Ouro) ---
        # Se recebermos a rodada, tentamos achar a DATA REAL desse jogo na base.
        # Isso substitui o date_cutoff manual e garante precisão cronológica absoluta.
        if rodada_curr is not None:
            # Buscar na base um jogo onde Time=Mandante, Adv=Visitante, Rodada=rodada_curr
            # Normalizar rodada para garantir match (int/float/str)
            try:
                # Filtrar
                mask = (
                    (self.df_pj["TIME"] == mandante) & 
                    (self.df_pj["ADVERSARIO"] == visitante) &
                    (self.df_pj["RODADA"].astype(str).str.replace(".0", "") == str(int(rodada_curr)))
                )
                match_row = self.df_pj[mask]
                
                if not match_row.empty:
                    # Achamos o jogo! Pegar a data.
                    auto_date = match_row.iloc[0]["DATA"]
                    if pd.notna(auto_date):
                        date_cutoff = auto_date
                        # print(f"DEBUG: Data Automática para {mandante}x{visitante} (R{rodada_curr}): {date_cutoff}")
            except Exception as e:
                # print(f"DEBUG: Falha ao buscar data automática: {e}")
                pass
        
        # Obter base bruta de meias (com o cutoff definido acima E filtro MV)
        df_raw = self.get_meias_stats_raw(date_cutoff, mv_filter=mv_filter)
        
        # Lógica de Filtros baseada no Modo
        if mando_mode == "POR_MANDO":
            filter_coc = "CASA"
            filter_cdf_opp = "CASA" # Opp jogou em Casa (logo Visitante estava Fora)
            filter_cof = "FORA"
            filter_cdc_opp = "FORA" # Opp jogou Fora (logo Mandante estava em Casa)
        else:
            # Modo TODOS: Pega geral (None)
            filter_coc = None
            filter_cdf_opp = None 
            filter_cof = None
            filter_cdc_opp = None
            
        # --- LADO ESQUERDO (Mandante) ---
        # 1. COC (Conquistados em Casa - Mandante)
        coc = self.get_aggregated_stats(df_raw, window_n, time_filter=mandante, mando_filter=filter_coc)
        
        # 2. CDF (Cedidos Fora - Visitante)
        # O CDF olha para os ADVERSÁRIOS do Visitante.
        # Se POR_MANDO: Visitante jogou Fora -> Adversario jogou Casa.
        # Se TODOS: Visitante jogou Qualquer -> Adversario jogou Qualquer.
        
        df_opp_vis = df_raw[df_raw["ADVERSARIO"] == visitante]
        if filter_cdf_opp:
             df_opp_vis = df_opp_vis[df_opp_vis["MANDO"] == filter_cdf_opp]
             
        cdf = self.get_aggregated_stats(df_opp_vis, window_n)
        
        # --- LADO DIREITO (Visitante) ---
        # 3. COF (Conquistados Fora - Visitante)
        cof = self.get_aggregated_stats(df_raw, window_n, time_filter=visitante, mando_filter=filter_cof)
        
        # 4. CDC (Cedidos em Casa - Mandante)
        # O CDC olha para os ADVERSÁRIOS do Mandante.
        df_opp_mand = df_raw[df_raw["ADVERSARIO"] == mandante]
        if filter_cdc_opp:
             df_opp_mand = df_opp_mand[df_opp_mand["MANDO"] == filter_cdc_opp]
             
        cdc = self.get_aggregated_stats(df_opp_mand, window_n)
        
        return {
            "MANDANTE": mandante,
            "VISITANTE": visitante,
            # COC
            "COC_G": coc["G"], "COC_A": coc["A"], "COC_PG": coc["PG"], "COC_CHUTES": coc["CHUTES"], "COC_AF": coc["AF"], "COC_DE": coc["DE"], "COC_BASICA": coc["BASICA"],
            # CDF
            "CDF_G": cdf["G"], "CDF_A": cdf["A"], "CDF_PG": cdf["PG"], "CDF_CHUTES": cdf["CHUTES"], "CDF_AF": cdf["AF"], "CDF_DE": cdf["DE"], "CDF_BASICA": cdf["BASICA"],
            # COF
            "COF_G": cof["G"], "COF_A": cof["A"], "COF_PG": cof["PG"], "COF_CHUTES": cof["CHUTES"], "COF_AF": cof["AF"], "COF_DE": cof["DE"], "COF_BASICA": cof["BASICA"],
            # CDC
            "CDC_G": cdc["G"], "CDC_A": cdc["A"], "CDC_PG": cdc["PG"], "CDC_CHUTES": cdc["CHUTES"], "CDC_AF": cdc["AF"], "CDC_DE": cdc["DE"], "CDC_BASICA": cdc["BASICA"],
        }

    def get_audit_trace(self, df_raw, window_n, time_filter=None, mando_filter=None):
        """
        Retorna o DataFrame detalhado dos jogos que compõem a métrica.
        Útil para auditoria.
        """
        # Reutiliza a lógica de filtro de get_aggregated_stats
        df = df_raw.copy()
        if time_filter:
            df = df[df["TIME"] == time_filter]
        if mando_filter == "CASA":
            df = df[df["MANDO"] == "CASA"]
        elif mando_filter == "FORA":
            df = df[df["MANDO"] == "FORA"]
            
        df = df.sort_values("DATA", ascending=True)
        
        # Agrupa POR JOGO
        game_stats = df.groupby(["MATCH_ID", "ADVERSARIO", "MANDO"]).agg({
            "PG": "sum",
            "CHUTES": "sum",
            "AF": "sum",
            "BASICA": "mean",
            "DATA": "first"
        }).sort_values("DATA").reset_index()
        
        if hasattr(game_stats, "tail"):
            slice_stats = game_stats.tail(window_n) if window_n > 0 else game_stats
        else:
            slice_stats = game_stats
            
        return slice_stats

    def get_player_concentration(self, team, position, window_n=3,
                                 mando_filter=None, date_cutoff=None):
        """Concentração dos scouts no jogador dentro da janela da tabela."""
        pos = str(position).upper()
        if pos in {"MEIAS", "VOLANTES", "ATACANTES"}:
            mv = {"MEIAS": "MEIA", "VOLANTES": "VOLANTE", "ATACANTES": "ATACANTE"}[pos]
            df = self.get_meias_stats_raw(date_cutoff, mv_filter=mv)
            metrics = {
                "MEIAS": ["PG", "CHUTES", "AF", "BASICA"],
                "VOLANTES": ["DE", "BASICA", "PG"],
                "ATACANTES": ["G", "A", "PG", "CHUTES", "BASICA"],
            }[pos]
        elif pos == "ZAGUEIROS":
            df = self.get_zagueiros_stats_raw(date_cutoff)
            metrics = ["DE", "CHUTES", "BASICA"]
        elif pos == "LATERAIS":
            raw = self.df_pj.copy()
            if date_cutoff is not None:
                raw = raw[raw["DATA"] < pd.to_datetime(date_cutoff)]
            real = pd.to_numeric(raw.get("POS_REAL"), errors="coerce")
            df = raw[real.round(1).isin([2.2, 2.6])].copy()
            df["DE"] = pd.to_numeric(df.get("DS", 0), errors="coerce").fillna(0)
            df["PG"] = pd.to_numeric(df.get("G", 0), errors="coerce").fillna(0) + pd.to_numeric(df.get("A", 0), errors="coerce").fillna(0)
            if "BASICA" not in df.columns:
                df["BASICA"] = pd.to_numeric(df.get("PONTOS", 0), errors="coerce").fillna(0)
            metrics = ["DE", "BASICA", "PG"]
        else:
            return pd.DataFrame()

        df = df[df["TIME"].eq(team)].copy()
        if mando_filter in {"CASA", "FORA"}:
            df = df[df["MANDO"].eq(mando_filter)]
        match_dates = df.groupby("MATCH_ID")["DATA"].first().sort_values().tail(window_n)
        df = df[df["MATCH_ID"].isin(match_dates.index)].copy()
        if df.empty:
            return pd.DataFrame()

        records = []
        for metric in metrics:
            if metric not in df.columns:
                continue
            values = pd.to_numeric(df[metric], errors="coerce").fillna(0)
            work = df.assign(_VALUE=values)
            aggregation = "mean" if metric == "BASICA" else "sum"
            players = work.groupby("NOME", as_index=False).agg(
                TOTAL=("_VALUE", aggregation),
                JOGOS=("MATCH_ID", "nunique"),
            )
            players = players[players["TOTAL"].gt(0)].sort_values(
                ["TOTAL", "JOGOS", "NOME"], ascending=[False, False, True]
            )
            total = players["TOTAL"].sum()
            if total <= 0:
                continue
            players["PARTICIPACAO"] = players["TOTAL"] / total
            players["CONCENTRACAO"] = pd.cut(
                players["PARTICIPACAO"],
                bins=[-np.inf, 0.35, 0.50, np.inf],
                labels=["DISTRIBUIDA", "RELEVANTE", "ALTA"],
                right=False,
            ).astype(str)
            players["TIME"] = team
            players["POSICAO"] = pos
            players["SCOUT"] = metric
            players["RANK"] = range(1, len(players) + 1)
            records.append(players.head(3))
        if not records:
            return pd.DataFrame()
        return pd.concat(records, ignore_index=True)[
            ["TIME", "POSICAO", "SCOUT", "RANK", "NOME", "TOTAL", "PARTICIPACAO", "CONCENTRACAO", "JOGOS"]
        ]

    def get_team_scout_context(self, team, position, metric, mando, date_cutoff=None):
        """Compara o recorte principal de 3 por mando com 5 e 10 gerais."""
        pos = str(position).upper()
        metric = str(metric).upper()
        if pos in {"MEIAS", "VOLANTES", "ATACANTES"}:
            mv = {"MEIAS": "MEIA", "VOLANTES": "VOLANTE", "ATACANTES": "ATACANTE"}[pos]
            df = self.get_meias_stats_raw(date_cutoff, mv_filter=mv)
        elif pos == "ZAGUEIROS":
            df = self.get_zagueiros_stats_raw(date_cutoff)
        elif pos == "LATERAIS":
            raw = self.df_pj.copy()
            if date_cutoff is not None:
                raw = raw[raw["DATA"] < pd.to_datetime(date_cutoff)]
            real = pd.to_numeric(raw.get("POS_REAL"), errors="coerce")
            df = raw[real.round(1).isin([2.2, 2.6])].copy()
            df["DE"] = pd.to_numeric(df.get("DS", 0), errors="coerce").fillna(0)
            df["PG"] = pd.to_numeric(df.get("G", 0), errors="coerce").fillna(0) + pd.to_numeric(df.get("A", 0), errors="coerce").fillna(0)
        else:
            return None
        if metric not in df.columns:
            return None
        df = df[df["TIME"].eq(team)].copy()
        agg = "mean" if metric == "BASICA" else "sum"
        games = df.groupby(["MATCH_ID", "MANDO"], as_index=False).agg(
            VALUE=(metric, agg), DATA=("DATA", "first")
        ).sort_values("DATA")
        primary = games[games["MANDO"].eq(mando)].tail(3)
        general5, general10 = games.tail(5), games.tail(10)
        if len(primary) < 3:
            return None
        calc = (lambda frame: frame.VALUE.mean()) if metric == "BASICA" else (lambda frame: frame.VALUE.sum())
        v3, v5, v10 = calc(primary), calc(general5), calc(general10)
        # Compara médias por jogo para que janelas diferentes sejam equivalentes.
        p3 = v3 if metric == "BASICA" else v3 / len(primary)
        p5 = v5 if metric == "BASICA" else v5 / max(len(general5), 1)
        p10 = v10 if metric == "BASICA" else v10 / max(len(general10), 1)
        if p5 >= p3 * 0.85 and p10 >= p3 * 0.75:
            status = "CONFIRMADO_5_E_10"
        elif p5 >= p3 * 0.85:
            status = "CONFIRMADO_5"
        elif p3 > p5 * 1.20:
            status = "CRESCIMENTO_RECENTE"
        else:
            status = "RECENTE_SEM_LASTRO"
        return {"TIME": team, "POSICAO": pos, "SCOUT": metric,
                "RECORTE_3_MANDO": v3, "RECORTE_5_GERAL": v5,
                "RECORTE_10_GERAL": v10, "STATUS": status}
    
    # --- ZAGUEIROS ENGINE ---
    def get_zagueiros_stats_raw(self, date_cutoff=None):
        """gathers raw stats for Zagueiros (Pos 3)"""
        # 1. Filtro Zagueiros (Pos 3)
        # Loader já renomeia "PosReal" para "POSICAO".
        # Usar config.POS_IDS["ZAGUEIRO"] para garantir compatibilidade com "3" e "3.0"
        
        target_ids = config.POS_IDS["ZAGUEIRO"] # ["3", "3.0"]
        mask = self.df_pj["POSICAO"].astype(str).isin(target_ids)
        df = self.df_pj[mask].copy()
        
        # 2. Filtro de Data
        if date_cutoff:
             df = df[df["DATA"] < pd.to_datetime(date_cutoff)]
             
        
        # 3. Métricas
        # DE (Desarmes) - Mapeando DS (Desarme) para variavel DE interna
        if "DS" in df.columns:
            df["DE"] = df["DS"]
        elif "DE" not in df.columns: 
            df["DE"] = 0
            
        # SG (Saldo de gols) - Bônus.
        if "SG" not in df.columns: df["SG"] = 0
        
        # CHUTES
        for col in ["FF", "FD", "FT"]:
             if col not in df.columns: df[col] = 0
        df["CHUTES"] = df["FF"] + df["FD"] + df["FT"]
        
        # PONTOS (Pts)
        if "PONTOS" not in df.columns: df["PONTOS"] = 0
        
        # BASICA
        if "BASICA" not in df.columns: df["BASICA"] = df["PONTOS"] # Fallback
        
        return df

    def get_zagueiros_aggregated(self, df_raw, window_n, time_filter=None, mando_filter=None):
        df = df_raw.copy()
        
        if time_filter: df = df[df["TIME"] == time_filter]
        
        if mando_filter == "CASA": df = df[df["MANDO"] == "CASA"]
        elif mando_filter == "FORA": df = df[df["MANDO"] == "FORA"]
        
        df = df.sort_values("DATA", ascending=True)
        
        # Agrupa POR JOGO
        # SG é do TIME. Se qualquer um tem SG, o time tem SG nesse jogo (vale 1).
        # DE, CHUTES: Soma de todos.
        # PTS, BASICA: Média dos jogadores.
        
        game_stats = df.groupby(["MATCH_ID", "ADVERSARIO", "MANDO"]).agg({
            "SG": "max",     # 1 se o time teve SG, 0 se não (basta pegar o max dos zagueiros)
            "DE": "sum",     # Soma da zaga
            "CHUTES": "sum", # Soma da zaga
            "PONTOS": "mean",# Média por jogador
            "BASICA": "mean",# Média por jogador
            "DATA": "first"
        }).sort_values("DATA").reset_index()
        
        # Janela
        if hasattr(game_stats, "tail"):
            slice_stats = game_stats.tail(window_n) if window_n > 0 else game_stats
        else:
            slice_stats = game_stats
            
        if len(slice_stats) == 0:
            return {k: 0 for k in ["SG", "DE", "CHUTES", "CHUTES_INDIV", "PONTOS", "BASICA"]} | {"CHUTES_JOGADOR": ""}

        selected = df[df["MATCH_ID"].isin(slice_stats["MATCH_ID"])]
        individual = selected.groupby("NOME")["CHUTES"].sum().sort_values(ascending=False)
        max_chutes = float(individual.iloc[0]) if not individual.empty else 0
        max_jogador = str(individual.index[0]) if not individual.empty else ""
            
        return {
            "SG": int(slice_stats["SG"].sum()),      # Soma de jogos com SG
            "DE": slice_stats["DE"].sum(),           # Soma
            "CHUTES": slice_stats["CHUTES"].sum(),   # Soma
            "CHUTES_INDIV": max_chutes,
            "CHUTES_JOGADOR": max_jogador,
            "PONTOS": slice_stats["PONTOS"].mean(),  # Média das médias
            "BASICA": slice_stats["BASICA"].mean()   # Média das médias
        }

    def generate_zagueiros_table(self, mandante, visitante, window_n=5, date_cutoff=None, mando_mode="POR_MANDO", rodada_curr=None):
        # Normalização de nomes
        def normalize_team_name(team):
             if team in config.TEAM_ALIASES: return config.TEAM_ALIASES[team]
             return team
        mandante = normalize_team_name(mandante)
        visitante = normalize_team_name(visitante)
        
        # Auto-cutoff (igual Meias)
        if rodada_curr is not None:
             # Tenta achar data desse jogo
             try:
                mask = (
                    (self.df_pj["TIME"] == mandante) & 
                    (self.df_pj["ADVERSARIO"] == visitante) &
                    (self.df_pj["RODADA"].astype(str).str.replace(".0", "") == str(int(rodada_curr)))
                )
                match_row = self.df_pj[mask]
                if not match_row.empty:
                    date_cutoff = match_row.iloc[0]["DATA"]
             except: pass

        df_raw = self.get_zagueiros_stats_raw(date_cutoff)
        
        # Filtros
        if mando_mode == "POR_MANDO":
            f_coc, f_cdf_opp = "CASA", "CASA"
            f_cof, f_cdc_opp = "FORA", "FORA"
        else:
            f_coc = f_cdf_opp = f_cof = f_cdc_opp = None
            
        # Lado Mandante
        coc = self.get_zagueiros_aggregated(df_raw, window_n, time_filter=mandante, mando_filter=f_coc)
        
        # CDF (Cedido pelo Adversário do Visitante quando Adv jogou em Casa => Visitante jogou Fora)
        # Visitante Adversaries
        df_opp_vis = df_raw[df_raw["ADVERSARIO"] == visitante]
        if f_cdf_opp: df_opp_vis = df_opp_vis[df_opp_vis["MANDO"] == f_cdf_opp]
        cdf = self.get_zagueiros_aggregated(df_opp_vis, window_n)
        
        # Lado Visitante
        cof = self.get_zagueiros_aggregated(df_raw, window_n, time_filter=visitante, mando_filter=f_cof)
        
        # CDC (Cedido pelo Adversário do Mandante)
        df_opp_mand = df_raw[df_raw["ADVERSARIO"] == mandante]
        if f_cdc_opp: df_opp_mand = df_opp_mand[df_opp_mand["MANDO"] == f_cdc_opp]
        cdc = self.get_zagueiros_aggregated(df_opp_mand, window_n)
        
        return {
            "MANDANTE": mandante, "VISITANTE": visitante,
            # COC
            "COC_SG": coc["SG"], "COC_DE": coc["DE"], "COC_CHUTES": coc["CHUTES"], "COC_CHUTES_INDIV": coc["CHUTES_INDIV"], "COC_CHUTES_JOGADOR": coc["CHUTES_JOGADOR"], "COC_PTS": coc["PONTOS"], "COC_BASICA": coc["BASICA"],
            # CDF
            "CDF_SG": cdf["SG"], "CDF_DE": cdf["DE"], "CDF_CHUTES": cdf["CHUTES"], "CDF_CHUTES_INDIV": cdf["CHUTES_INDIV"], "CDF_CHUTES_JOGADOR": cdf["CHUTES_JOGADOR"], "CDF_PTS": cdf["PONTOS"], "CDF_BASICA": cdf["BASICA"],
            # COF
            "COF_SG": cof["SG"], "COF_DE": cof["DE"], "COF_CHUTES": cof["CHUTES"], "COF_CHUTES_INDIV": cof["CHUTES_INDIV"], "COF_CHUTES_JOGADOR": cof["CHUTES_JOGADOR"], "COF_PTS": cof["PONTOS"], "COF_BASICA": cof["BASICA"],
            # CDC
            "CDC_SG": cdc["SG"], "CDC_DE": cdc["DE"], "CDC_CHUTES": cdc["CHUTES"], "CDC_CHUTES_INDIV": cdc["CHUTES_INDIV"], "CDC_CHUTES_JOGADOR": cdc["CHUTES_JOGADOR"], "CDC_PTS": cdc["PONTOS"], "CDC_BASICA": cdc["BASICA"]
        }
    def get_team_offensive_stats(self, team, window_n, mando_filter=None):
        """
        Calcula estatísticas OFENSIVAS do time (para coluna AMEAÇAS).
        Retorna: Chutes Feitos, Gols Feitos, Defesas Forçadas (no goleiro adversário).
        """
        # Filtrar jogos do time
        df = self.df_pj[self.df_pj["TIME"] == team].copy()
        
        if mando_filter:
            df = df[df["MANDO"] == mando_filter]
            
        # Ordenar e pegar janela
        match_dates = df.groupby("MATCH_ID")["DATA"].first().sort_values()
        if window_n > 0:
            match_dates = match_dates.tail(window_n)
        
        selected_matches = match_dates.index.tolist()
        
        if not selected_matches:
             return {"CHUTES": 0, "GOLS": 0, "DE_FORCADA": 0, "JOGOS_SEM_MARCAR": 0, "PCT_DE_FORCADA": 0.0}
             
        # 1. Chutes e Gols (Do próprio time) - Soma de todos jogadores
        mask_team = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] == team)
        df_team = self.df_pj[mask_team]
        
        # Chutes = FD + G (Desconsiderando FT por enquanto para ser conservador, ou incluir?)
        # Texto diz "Finalizações no alvo". FD + G é o padrão.
        chutes = df_team["FD"].sum() + df_team["G"].sum()
        gols = df_team["G"].sum()
        
        # 2. Defesas Forçadas (Busca no Goleiro Adversário)
        # Adversário é quem jogou NESSES matches mas NÃO é o time
        mask_opp_gk = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] != team) & (self.df_pj["POSICAO"].isin(config.POS_IDS["GOLEIRO"]))
        df_opp_gk = self.df_pj[mask_opp_gk]

        col_de = "DE" if "DE" in df_opp_gk.columns else "DD"
        de_forcada = df_opp_gk[col_de].sum() if col_de in df_opp_gk.columns else 0

        # 3. Jogos Sem Marcar — usa GS dos goleiros adversários (inclui gols contra;
        #    pode haver mais de 1 goleiro por jogo em caso de substituição ou lesão)
        gs_por_jogo = df_opp_gk.groupby("MATCH_ID")["GS"].sum() if "GS" in df_opp_gk.columns else pd.Series(dtype=float)
        jogos_sem_marcar = sum(1 for mid in selected_matches if gs_por_jogo.get(mid, 0) == 0)

        # 4. % DE por jogo (media dos percentuais individuais)
        # Spec: "É uma MÉDIA" - calcula % de cada jogo separadamente, depois tira a média
        pct_per_game = []
        col_de_global = "DE" if "DE" in self.df_pj.columns else "DD"
        for mid in selected_matches:
            opp_gk_m = self.df_pj[
                (self.df_pj["MATCH_ID"] == mid) &
                (self.df_pj["TIME"] != team) &
                (self.df_pj["POSICAO"].isin(config.POS_IDS["GOLEIRO"]))
            ]
            de_m = opp_gk_m[col_de_global].sum() if col_de_global in opp_gk_m.columns else 0
            # Usa GS do goleiro adversário: contabiliza gols contra e múltiplos goleiros
            gols_m = opp_gk_m["GS"].sum() if "GS" in opp_gk_m.columns else 0
            total_m = de_m + gols_m
            if total_m > 0:
                pct_per_game.append(de_m / total_m * 100.0)
        pct_de_forcada = sum(pct_per_game) / len(pct_per_game) if pct_per_game else 0.0

        return {
            "CHUTES": chutes,
            "GOLS": gols,
            "DE_FORCADA": de_forcada,
            "JOGOS_SEM_MARCAR": jogos_sem_marcar,
            "PCT_DE_FORCADA": pct_de_forcada,
        }

    def get_team_defensive_stats(self, team, window_n, mando_filter=None):
        """
        Calcula estatísticas DEFENSIVAS do time (para coluna OPORTUNIDADES e AMEAÇAS sofridas).
        Retorna: Chutes Sofridos, Gols Sofridos, Defesas Feitas (pelo meu GK), SG.
        """
        # Filtrar jogos do time
        df = self.df_pj[self.df_pj["TIME"] == team].copy()
        
        if mando_filter:
            df = df[df["MANDO"] == mando_filter]
            
        match_dates = df.groupby("MATCH_ID")["DATA"].first().sort_values()
        if window_n > 0:
            match_dates = match_dates.tail(window_n)
            
        selected_matches = match_dates.index.tolist()
        
        if not selected_matches:
             return {"CHUTES_CEDIDOS": 0, "GS": 0, "DE": 0, "SG": 0}
             
        # 1. Stats do Goleiro/Defesa (Meu Time)
        mask_team_gk = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] == team) & (self.df_pj["POSICAO"].isin(config.POS_IDS["GOLEIRO"]))
        df_gk = self.df_pj[mask_team_gk]

        col_de = "DE" if "DE" in df_gk.columns else "DD"
        de_feita = df_gk[col_de].sum() if col_de in df_gk.columns else 0

        # GS (Gols Sofridos) - do próprio goleiro
        gs = df_gk["GS"].sum() if "GS" in df_gk.columns else 0

        # SG (Saldo Gol) - Bônus do time. Pegar max por partida do time.
        mask_team = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] == team)
        df_team_all = self.df_pj[mask_team]
        sg = df_team_all.groupby("MATCH_ID")["SG"].max().sum()

        # 2. Chutes Sofridos (Soma chutes do Adversário)
        mask_opp = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] != team)
        df_opp = self.df_pj[mask_opp]
        chutes_cedidos = df_opp["FD"].sum() + df_opp["G"].sum()

        # 3. % DE por jogo (media dos percentuais individuais)
        # Spec: "É uma MÉDIA" - calcula % de cada jogo separadamente, depois tira a média
        pct_per_game = []
        col_de_global = "DE" if "DE" in self.df_pj.columns else "DD"
        for mid in selected_matches:
            gk_m = self.df_pj[
                (self.df_pj["MATCH_ID"] == mid) &
                (self.df_pj["TIME"] == team) &
                (self.df_pj["POSICAO"].isin(config.POS_IDS["GOLEIRO"]))
            ]
            de_m = gk_m[col_de_global].sum() if col_de_global in gk_m.columns else 0
            gs_m = gk_m["GS"].sum() if "GS" in gk_m.columns else 0
            total_m = de_m + gs_m
            if total_m > 0:
                pct_per_game.append(de_m / total_m * 100.0)
        pct_de = sum(pct_per_game) / len(pct_per_game) if pct_per_game else 0.0

        return {
            "CHUTES_CEDIDOS": chutes_cedidos,
            "GS": gs,
            "DE": de_feita,
            "SG": sg,
            "PCT_DE": pct_de,
        }

    def generate_goleiros_table(self, mandante, visitante, window_n=5, date_cutoff=None, mando_mode="POR_MANDO", rodada_curr=None):
        """
        Gera linha da tabela de Goleiros (Cruzamento de Ameaças e Oportunidades).
        Estrutura BLINDADA e isolada.
        """
        # Normalizar nomes
        def normalize(t): return config.TEAM_ALIASES.get(t, t)
        mandante = normalize(mandante)
        visitante = normalize(visitante)

        # Definir filtros de mando
        # Padrão: Mandante usa stats CASAS, Visitante usa stats FORA
        m_home = "CASA"
        m_away = "FORA"
        
        # Se filtro for GERAL, ignora mando
        if mando_mode == "TODOS":
            m_home = None
            m_away = None
            
        # === LADO ESQUERDO (MANDANTE CONTEXTO) ===
        # AMEAÇAS (Mandante Attack vs Visitante Defense)
        # COC: Mandante Attack
        man_off = self.get_team_offensive_stats(mandante, window_n, m_home)
        # CDF: Visitante Defense (Chutes Sofridos, Gols Sofridos)
        vis_def = self.get_team_defensive_stats(visitante, window_n, m_away)
        
        # OPORTUNIDADES (Visitante GK vs Mandante Yielding)
        # COF: Visitante GK Stats (DE, SG, %DE) -> Note: COF label usually means "Como Oponente Fora" (Visitante). Fits.
        # CDC: Mandante Yielding (Defesas Forçadas pelo Mandante)
        # CDC vem de `man_off["DE_FORCADA"]` (Defesas que o Mandante forçou)
        
        # === LADO DIREITO (VISITANTE CONTEXTO) ===
        # AMEAÇAS (Visitante Attack vs Mandante Defense)
        # COF: Visitante Attack
        vis_off = self.get_team_offensive_stats(visitante, window_n, m_away)
        # CDC: Mandante Defense
        man_def = self.get_team_defensive_stats(mandante, window_n, m_home)
        
        # OPORTUNIDADES (Mandante GK vs Visitante Yielding)
        # COC: Mandante GK Stats
        # CDF: Visitante Yielding (Defesas Forçadas pelo Visitante)
        
        # === CÁLCULOS DERIVADOS ===
        # CHUTES AG (Soma)
        # CHUT. PM (Chutes / Gols) - Evitar div por zero
        def calc_pm(chutes, gols):
            return (chutes / gols) if gols > 0 else 0.0
            
        # % DE (EFICIÊNCIA: DE / (DE+GS))
        def calc_pct(de, gs):
            total = de + gs
            return (de / total * 100.0) if total > 0 else 0.0
            
        return {
            "MANDANTE": mandante,
            "VISITANTE": visitante,
            "_WINDOW_N": window_n,
            
            # --- MANDANTE SIDE (Left Panel - Analisando Goleiro MANDANTE) ---
            # AMEACAS: Chutes do Visitante (COF) e Sofridos pelo Mandante (CDC)
            "COF_CHUTES_AG": vis_off["CHUTES"],      
            "CDC_CHUTES_AG": man_def["CHUTES_CEDIDOS"], 
            
            "COF_CHUTES_PM": calc_pm(vis_off["CHUTES"], vis_off["GOLS"]),
            "CDC_CHUTES_PM": calc_pm(man_def["CHUTES_CEDIDOS"], man_def["GS"]),
            
            "COF_GOLS": vis_off["GOLS"],
            "CDC_GOLS": man_def["GS"],
            
            # OPORTUNIDADES: Defesas do Mandante (COC) e Forçadas pelo Visitante (CDF)
            "COC_DE": man_def["DE"],        
            "CDF_DE": vis_off["DE_FORCADA"],
            
            "COC_SG": man_def["SG"],       
            "CDF_SG": vis_off["JOGOS_SEM_MARCAR"],
                         
            "COC_PCT_DE": man_def["PCT_DE"],
            "CDF_PCT_DE": vis_off["PCT_DE_FORCADA"],


            # --- VISITANTE SIDE (Right Panel - Analisando Goleiro VISITANTE) ---
            # AMEACAS: Chutes do Mandante (COC) e Sofridos pelo Visitante (CDF)
            "COC_CHUTES_AG": man_off["CHUTES"],         
            "CDF_CHUTES_AG": vis_def["CHUTES_CEDIDOS"], 
            
            "COC_CHUTES_PM": calc_pm(man_off["CHUTES"], man_off["GOLS"]),
            "CDF_CHUTES_PM": calc_pm(vis_def["CHUTES_CEDIDOS"], vis_def["GS"]),
            
            "COC_GOLS": man_off["GOLS"],
            "CDF_GOLS": vis_def["GS"],
            
            # OPORTUNIDADES: Defesas do Visitante (COF) e Forçadas pelo Mandante (CDC)
            "COF_DE": vis_def["DE"],           
            "CDC_DE": man_off["DE_FORCADA"],   
            
            "COF_SG": vis_def["SG"],           
            "CDC_SG": man_off["JOGOS_SEM_MARCAR"],
            
            "COF_PCT_DE": vis_def["PCT_DE"],
            "CDC_PCT_DE": man_off["PCT_DE_FORCADA"],
        }

    # -------------------------------------------------------------------------
    #                            LATERAIS (LE / LD)
    # -------------------------------------------------------------------------

    def get_laterais_aggregated(self, df_raw, window_n, time_filter=None, mando_filter=None):
        """
        Agrega estatísticas de Laterais (LE e LD) para um time específico.
        """
        df = df_raw.copy()
        
        if df.empty:
             return {
                "LE_DE": 0, "LE_PG": 0, "LE_BASICA": 0.0,
                "LD_DE": 0, "LD_PG": 0, "LD_BASICA": 0.0,
                "SG": 0
            }
        
        # Filtros Básicos
        if time_filter: df = df[df["TIME"] == time_filter]
        
        if mando_filter == "CASA": df = df[df["MANDO"] == "CASA"]
        elif mando_filter == "FORA": df = df[df["MANDO"] == "FORA"]
        
        # Sort e Janela de JOGOS (Time-Adversário)
        match_dates = df.groupby(["MATCH_ID", "DATA"]).first().sort_values("DATA")
        
        if window_n > 0:
            match_dates = match_dates.tail(window_n)
            
        selected_matches = [idx[0] for idx in match_dates.index]
        
        if not selected_matches:
            # Retorno vazio zerado
            return {
                "LE_DE": 0, "LE_PG": 0, "LE_BASICA": 0.0,
                "LD_DE": 0, "LD_PG": 0, "LD_BASICA": 0.0,
                "SG": 0
            }
            
        # Filtrar o DF principal apenas com os jogos selecionados
        df = df[df["MATCH_ID"].isin(selected_matches)]
        
        def is_le(pos):
             try: return abs(float(pos) - 2.6) < 0.01
             except: return False
             
        def is_ld(pos):
             try: return abs(float(pos) - 2.2) < 0.01
             except: return False

        # --- CÁLCULO DAS MÉTRICAS ---
        
        # 1. SG (Clean Sheet do TIME) - Do Time no Jogo
        # Agrupa por match e pega o max de SG (se alguem teve SG=1, o time teve)
        jogos_sg = df.groupby("MATCH_ID")["SG"].max().sum()
        
        # 2. LE Stats
        mask_le = df["POS_REAL"].apply(is_le)
        df_le = df[mask_le]
        
        le_de = df_le["DS"].sum()
        le_pg = (df_le["G"] + df_le["A"]).sum()
        le_basica = df_le["BASICA"].mean() if len(df_le) > 0 else 0.0
        
        # 3. LD Stats
        mask_ld = df["POS_REAL"].apply(is_ld)
        df_ld = df[mask_ld]
        
        ld_de = df_ld["DS"].sum()
        ld_pg = (df_ld["G"] + df_ld["A"]).sum()
        ld_basica = df_ld["BASICA"].mean() if len(df_ld) > 0 else 0.0
        
        return {
            "LE_DE": le_de,
            "LE_PG": le_pg,
            "LE_BASICA": le_basica,
            "LD_DE": ld_de,
            "LD_PG": ld_pg,
            "LD_BASICA": ld_basica,
            "SG": int(jogos_sg)
        }

    def generate_laterais_table(self, mandante, visitante, window_n=5, date_cutoff=None, mando_mode="POR_MANDO", rodada_curr=None):
        # 1. Normalizar e converter para MAIÚSCULAS (df_pj usa MAIÚSCULAS)
        mandante = config.TEAM_ALIASES.get(mandante, mandante).upper()
        visitante = config.TEAM_ALIASES.get(visitante, visitante).upper()
        
        # 2. Configurar Filtros
        if mando_mode == "POR_MANDO":
            f_home = "CASA"
            f_away = "FORA"
        else:
            f_home = None
            f_away = None
            
        # 3. Preparar DF Raw (Todos os jogos, para poder buscar adversários)
        df_all = self.df_pj.copy()
        
        # Auto-cutoff
        if rodada_curr is not None:
             try:
                mask = (
                    (self.df_pj["TIME"] == mandante) & 
                    (self.df_pj["ADVERSARIO"] == visitante) &
                    (self.df_pj["RODADA"].astype(str).str.replace(".0", "") == str(int(rodada_curr)))
                )
                match_row = self.df_pj[mask]
                if not match_row.empty:
                    df_all = df_all[df_all["DATA"] < match_row.iloc[0]["DATA"]]
             except: pass
             
        # === LADO ESQUERDO (MANDANTE) ===
        # Filtro: Jogos do Mandante (em Casa)
        matches_man = df_all[df_all["TIME"] == mandante]
        if f_home: matches_man = matches_man[matches_man["MANDO"] == f_home]
        
        # Pegar janela
        if matches_man.empty:
            coc_stats = self.get_laterais_aggregated(pd.DataFrame(), 0)
            cdc_stats = self.get_laterais_aggregated(pd.DataFrame(), 0) # CDC: Cedido pelo Mandante (adversários do mandante)
        else:
            match_dates = matches_man.groupby("MATCH_ID")["DATA"].first().sort_values().tail(window_n)
            selected_ids_man = match_dates.index.tolist()
            
            # COC: Stats do Mandante
            df_man_games = df_all[(df_all["MATCH_ID"].isin(selected_ids_man)) & (df_all["TIME"] == mandante)]
            coc_stats = self.get_laterais_aggregated(df_man_games, 0)
            
            # CDC: Stats dos Adversários do Mandante (Cedidos pelo Mandante)
            # Na tabela, CDC fica na Direita (lado do Visitante)
            df_opp_man_games = df_all[(df_all["MATCH_ID"].isin(selected_ids_man)) & (df_all["TIME"] != mandante)]
            cdc_stats = self.get_laterais_aggregated(df_opp_man_games, 0)
        
        # === LADO DIREITO (VISITANTE) ===
        # Filtro: Jogos do Visitante (Fora)
        matches_vis = df_all[df_all["TIME"] == visitante]
        if f_away: matches_vis = matches_vis[matches_vis["MANDO"] == f_away]
        
        if matches_vis.empty:
            cof_stats = self.get_laterais_aggregated(pd.DataFrame(), 0)
            cdf_stats = self.get_laterais_aggregated(pd.DataFrame(), 0) # CDF: Cedido pelo Visitante (adversários do visitante)
        else:
            match_dates_v = matches_vis.groupby("MATCH_ID")["DATA"].first().sort_values().tail(window_n)
            selected_ids_vis = match_dates_v.index.tolist()
            
            # COF: Stats do Visitante
            df_vis_games = df_all[(df_all["MATCH_ID"].isin(selected_ids_vis)) & (df_all["TIME"] == visitante)]
            cof_stats = self.get_laterais_aggregated(df_vis_games, 0)
            
            # CDF: Stats dos Adversários do Visitante (Cedidos pelo Visitante)
            # Na tabela, CDF fica na Esquerda (lado do Mandante)
            df_opp_vis_games = df_all[(df_all["MATCH_ID"].isin(selected_ids_vis)) & (df_all["TIME"] != visitante)]
            cdf_stats = self.get_laterais_aggregated(df_opp_vis_games, 0)
        
        return {
            "MANDANTE": mandante, "VISITANTE": visitante,
            
            # --- MANDANTE (LEFT) ---
            # LE
            "COC_LE_DE": coc_stats["LE_DE"], "CDF_LE_DE": cdf_stats["LE_DE"],
            "COC_LE_PG": coc_stats["LE_PG"], "CDF_LE_PG": cdf_stats["LE_PG"],
            "COC_LE_BAS": coc_stats["LE_BASICA"], "CDF_LE_BAS": cdf_stats["LE_BASICA"],
            # LD
            "COC_LD_DE": coc_stats["LD_DE"], "CDF_LD_DE": cdf_stats["LD_DE"],
            "COC_LD_PG": coc_stats["LD_PG"], "CDF_LD_PG": cdf_stats["LD_PG"],
            "COC_LD_BAS": coc_stats["LD_BASICA"], "CDF_LD_BAS": cdf_stats["LD_BASICA"],
            # SG
            "COC_SG": coc_stats["SG"], "CDF_SG": cdf_stats["SG"],
            
            # --- VISITANTE (RIGHT) ---
            # SG
            "COF_SG": cof_stats["SG"], "CDC_SG": cdc_stats["SG"],
            # LD
            "COF_LD_DE": cof_stats["LD_DE"], "CDC_LD_DE": cdc_stats["LD_DE"],
            "COF_LD_PG": cof_stats["LD_PG"], "CDC_LD_PG": cdc_stats["LD_PG"],
            "COF_LD_BAS": cof_stats["LD_BASICA"], "CDC_LD_BAS": cdc_stats["LD_BASICA"],
            # LE
            "COF_LE_DE": cof_stats["LE_DE"], "CDC_LE_DE": cdc_stats["LE_DE"],
            "COF_LE_PG": cof_stats["LE_PG"], "CDC_LE_PG": cdc_stats["LE_PG"],
            "COF_LE_BAS": cof_stats["LE_BASICA"], "CDC_LE_BAS": cdc_stats["LE_BASICA"],
        }

    # -------------------------------------------------------------------------
    #                    MOTOR INVISIVEL - PERFIS DE GOLEIROS
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_goalkeeper_profiles(gol_row):
        """
        Calcula indices e perfil para os dois goleiros de um confronto.

        Recebe o dict retornado por generate_goleiros_table() e retorna
        uma lista com dois dicts (mandante, visitante).
        Nao altera nenhuma logica visual nem de renderizacao.

        Os caminhos de defesas e SG são classificados de forma independente.
        """
        def safe(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        window_n = max(int(safe(gol_row.get("_WINDOW_N", 3))), 1)
        factor = window_n / 3.0

        def scaled(value):
            return value * factor

        def defense_level(own_saves, opponent_sot):
            # Ambos precisam confirmar a oportunidade. Volume de um lado só não basta.
            if own_saves >= scaled(12) and opponent_sot >= scaled(12):
                return "FORTE"
            if own_saves >= scaled(11) and opponent_sot >= scaled(12):
                return "BOM"
            if own_saves >= scaled(10) and opponent_sot >= scaled(10):
                return "SINAL"
            return "-"

        def sg_level(own_sg, opponent_blanks, opponent_goals):
            # SG é um caminho defensivo; pressão para defesas não interfere aqui.
            if own_sg >= scaled(2) and opponent_goals <= scaled(4):
                return "FORTE"
            if (own_sg >= scaled(1) and opponent_blanks >= scaled(1)
                    and opponent_goals <= scaled(3)):
                return "BOM"
            if own_sg >= scaled(1) and opponent_goals <= scaled(4):
                return "SINAL"
            return "-"

        def synthesize(def_level, sg_level, opponent_goals, own_goals_conceded):
            has_def = def_level != "-"
            has_sg = sg_level != "-"
            if has_def and has_sg:
                return "AMBOS"
            if has_def:
                return "DEFESAS"
            if has_sg:
                return "SG"
            # Sem sinal positivo, a célula precisa comunicar risco claramente.
            if opponent_goals >= scaled(5) and own_goals_conceded >= scaled(4):
                return "ALTO_RISCO"
            return "RISCO"

        mandante = gol_row.get("MANDANTE", "")
        visitante = gol_row.get("VISITANTE", "")
        jogo = f"{mandante} x {visitante}"

        # --- Indices do MANDANTE ---
        # SG_INDEX = COC_SG (SG do mandante em casa) + CDF_SG (SG cedido pelo visitante fora)
        man_sg = safe(gol_row.get("COC_SG", 0)) + safe(gol_row.get("CDF_SG", 0))
        # PRESSAO_INDEX = (COF_CHUTES_AG + CDC_CHUTES_AG) / 2
        man_pressao = round((safe(gol_row.get("COF_CHUTES_AG", 0)) + safe(gol_row.get("CDC_CHUTES_AG", 0))) / 2, 2)
        # DEFESAS_INDEX = (COC_DE + CDF_DE) / 2
        man_defesas = round((safe(gol_row.get("COC_DE", 0)) + safe(gol_row.get("CDF_DE", 0))) / 2, 2)
        # RISCO_INDEX = (COF_GOLS + CDC_GOLS) / 2
        man_risco = round((safe(gol_row.get("COF_GOLS", 0)) + safe(gol_row.get("CDC_GOLS", 0))) / 2, 2)
        # CHUTE_PM_CRUZADO = (COF_CHUTES_PM + CDC_CHUTES_PM) / 2  [apenas diagnostico]
        man_chute_pm = round((safe(gol_row.get("COF_CHUTES_PM", 0)) + safe(gol_row.get("CDC_CHUTES_PM", 0))) / 2, 2)
        # Dados brutos para BLOQUEIO e DEFESA_ROBUSTA (MANDANTE)
        man_gols_rival      = safe(gol_row.get("COF_GOLS", 0))
        man_gols_tc         = safe(gol_row.get("CDC_GOLS", 0))
        man_pm_rival        = safe(gol_row.get("COF_CHUTES_PM", 0))
        man_pm_tc           = safe(gol_row.get("CDC_CHUTES_PM", 0))
        man_defesas_time    = safe(gol_row.get("COC_DE", 0))
        man_defesas_rival   = safe(gol_row.get("CDF_DE", 0))
        man_def_level = defense_level(man_defesas_time, safe(gol_row.get("COF_CHUTES_AG", 0)))
        man_sg_level = sg_level(
            safe(gol_row.get("COC_SG", 0)),
            safe(gol_row.get("CDF_SG", 0)),
            safe(gol_row.get("COF_GOLS", 0)),
        )

        # --- Indices do VISITANTE ---
        # SG_INDEX = COF_SG (SG do visitante fora) + CDC_SG (SG cedido pelo mandante em casa)
        vis_sg = safe(gol_row.get("COF_SG", 0)) + safe(gol_row.get("CDC_SG", 0))
        # PRESSAO_INDEX = (COC_CHUTES_AG + CDF_CHUTES_AG) / 2
        vis_pressao = round((safe(gol_row.get("COC_CHUTES_AG", 0)) + safe(gol_row.get("CDF_CHUTES_AG", 0))) / 2, 2)
        # DEFESAS_INDEX = (COF_DE + CDC_DE) / 2
        vis_defesas = round((safe(gol_row.get("COF_DE", 0)) + safe(gol_row.get("CDC_DE", 0))) / 2, 2)
        # RISCO_INDEX = (COC_GOLS + CDF_GOLS) / 2
        vis_risco = round((safe(gol_row.get("COC_GOLS", 0)) + safe(gol_row.get("CDF_GOLS", 0))) / 2, 2)
        # CHUTE_PM_CRUZADO = (COC_CHUTES_PM + CDF_CHUTES_PM) / 2  [apenas diagnostico]
        vis_chute_pm = round((safe(gol_row.get("COC_CHUTES_PM", 0)) + safe(gol_row.get("CDF_CHUTES_PM", 0))) / 2, 2)
        # Dados brutos para BLOQUEIO e DEFESA_ROBUSTA (VISITANTE)
        vis_gols_rival      = safe(gol_row.get("COC_GOLS", 0))
        vis_gols_tc         = safe(gol_row.get("CDF_GOLS", 0))
        vis_pm_rival        = safe(gol_row.get("COC_CHUTES_PM", 0))
        vis_pm_tc           = safe(gol_row.get("CDF_CHUTES_PM", 0))
        vis_defesas_time    = safe(gol_row.get("COF_DE", 0))
        vis_defesas_rival   = safe(gol_row.get("CDC_DE", 0))
        vis_def_level = defense_level(vis_defesas_time, safe(gol_row.get("COC_CHUTES_AG", 0)))
        vis_sg_level = sg_level(
            safe(gol_row.get("COF_SG", 0)),
            safe(gol_row.get("CDC_SG", 0)),
            safe(gol_row.get("COC_GOLS", 0)),
        )

        return [
            {
                "JOGO": jogo,
                "TIME": mandante,
                "MANDO": "MANDANTE",
                "SG_INDEX": round(man_sg, 2),
                "PRESSAO_INDEX": man_pressao,
                "DEFESAS_INDEX": man_defesas,
                "RISCO_INDEX": man_risco,
                "CHUTE_PM_CRUZADO": man_chute_pm,
                "DEFESAS_NIVEL": man_def_level,
                "SG_NIVEL": man_sg_level,
                "PERFIL": synthesize(man_def_level, man_sg_level, man_gols_rival, man_gols_tc),
            },
            {
                "JOGO": jogo,
                "TIME": visitante,
                "MANDO": "VISITANTE",
                "SG_INDEX": round(vis_sg, 2),
                "PRESSAO_INDEX": vis_pressao,
                "DEFESAS_INDEX": vis_defesas,
                "RISCO_INDEX": vis_risco,
                "CHUTE_PM_CRUZADO": vis_chute_pm,
                "DEFESAS_NIVEL": vis_def_level,
                "SG_NIVEL": vis_sg_level,
                "PERFIL": synthesize(vis_def_level, vis_sg_level, vis_gols_rival, vis_gols_tc),
            },
        ]
