import pandas as pd
import numpy as np
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
        if process_new_upload(self.df_scouts, self.df_pj):
            return "Histórico atualizado com sucesso!"
        else:
            return "Nenhuma nova alteração de AF detectada ou erro no processamento."

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
            df["CLASSIFICACAO_MV"] = df["NOME"].str.upper().map(self.classificacao_mv)
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
            "PG": "sum",
            "CHUTES": "sum",
            "AF": "sum",
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
            return {k: 0 for k in ["PG", "CHUTES", "AF", "BASICA"]}
            
        return {
            "PG": slice_stats["PG"].sum(), # Soma na janela! (Documento: 'Método: SOMA')
            "CHUTES": slice_stats["CHUTES"].sum(), # SOMA
            "AF": slice_stats["AF"].sum(), # SOMA
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
            "COC_PG": coc["PG"], "COC_CHUTES": coc["CHUTES"], "COC_AF": coc["AF"], "COC_BASICA": coc["BASICA"],
            # CDF
            "CDF_PG": cdf["PG"], "CDF_CHUTES": cdf["CHUTES"], "CDF_AF": cdf["AF"], "CDF_BASICA": cdf["BASICA"],
            # COF
            "COF_PG": cof["PG"], "COF_CHUTES": cof["CHUTES"], "COF_AF": cof["AF"], "COF_BASICA": cof["BASICA"],
            # CDC
            "CDC_PG": cdc["PG"], "CDC_CHUTES": cdc["CHUTES"], "CDC_AF": cdc["AF"], "CDC_BASICA": cdc["BASICA"],
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
    
    # --- ZAGUEIROS ENGINE ---
    def get_zagueiros_stats_raw(self, date_cutoff=None):
        """gathers raw stats for Zagueiros (Pos 3)"""
        # 1. Filtro Zagueiros (Pos 3)
        # Loader já renomeia "PosReal" para "POSICAO".
        # Usar config.POS_IDS["ZAGUEIRO"] para garantir compatibilidade com "3" e "3.0"
        
        target_ids = config.POS_IDS["ZAGUEIRO"] # ["3", "3.0"]
        mask = self.df_pj["POSICAO"].astype(str).isin(target_ids)
        df = self.df_pj[mask].copy()
        
        print(f"DEBUG: get_zagueiros_stats_raw - Total Rows: {len(self.df_pj)} | Zagueiros Found: {len(df)}")
        if len(df) == 0:
             print(f"DEBUG: No Zagueiros found! Unique POSICAO values: {self.df_pj['POSICAO'].unique()}")
        
        
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
            return {k: 0 for k in ["SG", "DE", "CHUTES", "PONTOS", "BASICA"]}
            
        return {
            "SG": int(slice_stats["SG"].sum()),      # Soma de jogos com SG
            "DE": slice_stats["DE"].sum(),           # Soma
            "CHUTES": slice_stats["CHUTES"].sum(),   # Soma
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
            "COC_SG": coc["SG"], "COC_DE": coc["DE"], "COC_CHUTES": coc["CHUTES"], "COC_PTS": coc["PONTOS"], "COC_BASICA": coc["BASICA"],
            # CDF
            "CDF_SG": cdf["SG"], "CDF_DE": cdf["DE"], "CDF_CHUTES": cdf["CHUTES"], "CDF_PTS": cdf["PONTOS"], "CDF_BASICA": cdf["BASICA"],
            # COF
            "COF_SG": cof["SG"], "COF_DE": cof["DE"], "COF_CHUTES": cof["CHUTES"], "COF_PTS": cof["PONTOS"], "COF_BASICA": cof["BASICA"],
            # CDC
            "CDC_SG": cdc["SG"], "CDC_DE": cdc["DE"], "CDC_CHUTES": cdc["CHUTES"], "CDC_PTS": cdc["PONTOS"], "CDC_BASICA": cdc["BASICA"]
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
             return {"CHUTES": 0, "GOLS": 0, "DE_FORCADA": 0}
             
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
        
        # DE (Defesa Dificil) ou DS? Config diz DE -> DEFESA_DIFICIL
        # Vamos somar DE (que já foi carregada como DD no loader se mapeada)
        # Se 'DE' não existir, tenta 'DD'
        col_de = "DE" if "DE" in df_opp_gk.columns else "DD"
        de_forcada = df_opp_gk[col_de].sum() if col_de in df_opp_gk.columns else 0
        
        # 3. Jogos Sem Marcar (SG do Adversário)
        # Quantidade de jogos onde o time fez 0 gols
        # Agrupar por match para ver gols do time em cada jogo
        goals_per_match = df_team.groupby("MATCH_ID")["G"].sum()
        jogos_sem_marcar = (goals_per_match == 0).sum()
        
        return {
            "CHUTES": chutes,
            "GOLS": gols,
            "DE_FORCADA": de_forcada,
            "JOGOS_SEM_MARCAR": jogos_sem_marcar
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
        
        # DE (Defesas)
        col_de = "DE" if "DE" in df_gk.columns else "DD"
        de_feita = df_gk[col_de].sum() if col_de in df_gk.columns else 0
        
        # GS (Gols Sofridos) - As vezes GS está no goleiro, as vezes na zaga. Melhor pegar do Goleiro.
        gs = df_gk["GS"].sum() if "GS" in df_gk.columns else 0
        
        # SG (Saldo Gol) - Bônus do time. Pegar max por partida do time.
        mask_team = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] == team)
        df_team_all = self.df_pj[mask_team]
        # Agrupa por match e pega max de SG (se alguem teve SG, o time teve)
        sg = df_team_all.groupby("MATCH_ID")["SG"].max().sum()
        
        # 2. Chutes Sofridos (Soma chutes do Adversário)
        mask_opp = self.df_pj["MATCH_ID"].isin(selected_matches) & (self.df_pj["TIME"] != team)
        df_opp = self.df_pj[mask_opp]
        
        chutes_cedidos = df_opp["FD"].sum() + df_opp["G"].sum()
        
        return {
            "CHUTES_CEDIDOS": chutes_cedidos,
            "GS": gs,
            "DE": de_feita,
            "SG": sg
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
                         
            "COC_PCT_DE": calc_pct(man_def["DE"], man_def["GS"]),
            "CDF_PCT_DE": calc_pct(vis_off["DE_FORCADA"], vis_off["GOLS"]),


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
            
            "COF_PCT_DE": calc_pct(vis_def["DE"], vis_def["GS"]),
            "CDC_PCT_DE": calc_pct(man_off["DE_FORCADA"], man_off["GOLS"]),
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
