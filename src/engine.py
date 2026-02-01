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
        meia_ids = config.POS_IDS["MEIA_ONLY"]
        df = self.df_pj[self.df_pj["POSICAO"].astype(str).isin(meia_ids)].copy()
        
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
