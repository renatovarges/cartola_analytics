import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o diretório raiz ao sys.path para permitir "from src.engine ..."
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import os

st.set_page_config(page_title="Cartola Analytics 2026", layout="wide")

st.title("⚽ Cartola Analytics 2026 - Painel de Dados")

from src.rounds import parse_rounds_file
# ... imports anteriores

# Sidebar - Configurações
st.sidebar.header("Parâmetros da Análise")

# 1. Carregar Arquivo de Rodadas
ROUNDS_FILE = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\RODADAS_BRASILEIRAO_2026.txt"
rounds_data = {}
if os.path.exists(ROUNDS_FILE):
    rounds_data = parse_rounds_file(ROUNDS_FILE)
    st.sidebar.success(f"Tabela carregada: {len(rounds_data)} rodadas.")
else:
    st.sidebar.error("Arquivo de rodadas não encontrado.")

# 2. Seletor de Rodada Alvo
rodadas_disponiveis = sorted(rounds_data.keys()) if rounds_data else [1]
rodada_alvo = st.sidebar.selectbox("Rodada Alvo", rodadas_disponiveis, index=0)

# 3. Recorte e Filtros
window_n = st.sidebar.number_input("Recorte (N Jogos)", min_value=1, max_value=20, value=5)
tipo_filtro = st.sidebar.radio("Tipo de Filtro", ["TODOS", "POR_MANDO"], index=0, help="TODOS: Últimos N jogos gerais. POR_MANDO: Últimos N jogos em casa (para mandante) ou fora (para visitante).")

# Filtro de Clasificação (Meia vs Volante)
mv_selection = st.sidebar.radio("Classificação", ["Todos", "Apenas Meias", "Apenas Volantes"], index=0)
mv_filter_map = {"Todos": None, "Apenas Meias": "MEIA", "Apenas Volantes": "VOLANTE"}
mv_filter_val = mv_filter_map[mv_selection]

data_corte = st.sidebar.date_input("Data de Corte", pd.to_datetime("2026-12-31")) # Atualizado padrao pra 2026

# 4. Seleção de Arquivo Excel (Fonte de Dados)
DEFAULT_PATH = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

# Opção de upload
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fonte de Dados")
use_upload = st.sidebar.checkbox("Usar planilha personalizada", value=False, 
                                   help="Marque para fazer upload de uma planilha ao invés de usar a padrão")

file_path = DEFAULT_PATH
uploaded_file = None

if use_upload:
    uploaded_file = st.sidebar.file_uploader(
        "Carregar Excel", 
        type=["xlsx"],
        help="Faça upload da planilha Scouts_Reorganizado.xlsx atualizada"
    )
    if uploaded_file is not None:
        # Salvar temporariamente para usar com a engine
        temp_path = os.path.join(os.path.dirname(DEFAULT_PATH), "temp_upload.xlsx")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_path = temp_path
        st.sidebar.success(f"✅ Planilha carregada: {uploaded_file.name}")
    else:
        st.sidebar.warning("⚠️ Aguardando upload...")
        file_path = None
else:
    if os.path.exists(DEFAULT_PATH):
        st.sidebar.info(f"📁 Usando planilha padrão")
    else:
        st.sidebar.error("❌ Planilha padrão não encontrada")
        file_path = None

# Inicializar Engine
# @st.cache_resource  # Temporariamente desabilitado para debug
def get_engine_v2(path):
    return CartolaEngine(path)

# Validar se temos arquivo para processar
if file_path is None:
    st.error("❌ Nenhuma planilha disponível. Por favor, faça upload ou verifique se a planilha padrão existe.")
    st.stop()

try:
    engine = get_engine_v2(file_path)
    
    # --- GERENCIAMENTO DE HISTÓRICO AF ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Histórico de AF")
    
    if st.sidebar.button("Processar Atualização de AF", help="Clique aqui apenas quando subir um arquivo NOVO com scouts atualizados."):
        with st.sidebar.status("Processando AF...", expanded=True) as status:
            msg = engine.process_af_update()
            if "sucesso" in msg:
                status.update(label="✅ Sucesso!", state="complete")
                st.sidebar.success(msg)
            else:
                status.update(label="ℹ️ Info", state="complete")
                st.sidebar.info(msg)
                
except Exception as e:
    st.error(f"Erro ao carregar engine: {e}")
    st.stop()

# --- ABA MEIAS ---
st.header(f"Análise de Meias - Rodada {rodada_alvo}")

# Determinar Confrontos da Lista
confrontos = rounds_data.get(rodada_alvo, [])

if not confrontos:
    st.warning("Nenhum confronto encontrado para esta rodada.")
else:
    st.info(f"Processando {len(confrontos)} jogos da Rodada {rodada_alvo}...")

# Botão para (re)calcular
if st.button("Gerar Tabela de Meias", type="primary"):
    results = []
    progress_bar = st.progress(0)
    
    for i, (mandante, visitante) in enumerate(confrontos):
        try:
             row = engine.generate_confronto_table(
                mandante, 
                visitante, 
                window_n, 
                data_corte,
                mando_mode=tipo_filtro,
                rodada_curr=rodada_alvo, # REGRA DE OURO: Data automática
                mv_filter=mv_filter_val
            )
             results.append(row)
        except Exception as e:
            st.warning(f"Erro em {mandante}x{visitante}: {e}")
            
        progress_bar.progress((i + 1) / len(confrontos))

    if results:
        # Salvar no session_state
        st.session_state["meias_results"] = pd.DataFrame(results)
    else:
        st.warning("Nenhum dado gerado.")

# Lógica de Exibição (Baseado no Estado)
if "meias_results" in st.session_state:
    df_results = st.session_state["meias_results"]
    
    # Colunas e Ordem (Layout Centralizado)
    # Esquerda (Mandante em Casa + Visitante Fora que cedeu)
    left_cols = ["COC_AF", "CDF_AF", "COC_CHUTES", "CDF_CHUTES", "COC_PG", "CDF_PG", "COC_BASICA", "CDF_BASICA"]
    # Centro (Times)
    center_cols = ["MANDANTE", "VISITANTE"]
    # Direita (Visitante Fora + Mandante Casa que cedeu)
    right_cols = ["COF_BASICA", "CDC_BASICA", "COF_PG", "CDC_PG", "COF_CHUTES", "CDC_CHUTES", "COF_AF", "CDC_AF"]
    
    # Combinar e verificar quais existem no DF
    final_cols = []
    for c in left_cols + center_cols + right_cols:
        if c in df_results.columns:
            final_cols.append(c)
            
    # Reordenar DataFrame
    df_results = df_results[final_cols]
    
    # Exibir Tabela
    st.dataframe(df_results, use_container_width=True)
    
    # Botão Download CSV
    csv = df_results.to_csv(index=False).encode('utf-8-sig')
    col_dl1, col_dl2 = st.columns(2)
    col_dl1.download_button("Baixar CSV", csv, "tabela_meias.csv", "text/csv")
    
    # Botão Gerar PNG
    import matplotlib.pyplot as plt
    from src import renderer_v2 as renderer
    
    if col_dl2.button("📸 Gerar Tabela PNG"):
        with st.spinner("Desenhando tabela em alta resolução..."):
            try:
                # Usa o dataframe ORIGINAL DO RESULTADO (results no session state tem colunas brutas)
                # Precisamos passar o DF session_state["meias_results"] que ja tem os dados
                df_to_render = st.session_state["meias_results"]
                
                fig = renderer.render_meias_table(df_to_render, rodada_alvo, window_n, tipo_filtro)
                
                # Salvar em buffer
                from io import BytesIO
                buf = BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches='tight', facecolor='white')
                st.image(buf, caption="Tabela Gerada", width="stretch")
                
                # Download PNG
                st.download_button(
                    label="Baixar Imagem PNG",
                    data=buf.getvalue(),
                    file_name=f"tabela_meias_rodada_{rodada_alvo}.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {e}")
                import traceback
                st.text(traceback.format_exc())


# --- AUDITORIA ---
st.divider()
st.subheader("🕵️ Auditoria de Dados")

with st.expander("Abrir Painel de Auditoria"):
    col_audit1, col_audit2, col_audit3 = st.columns(3)
    
    # Seletores
    # Obter lista de times única do Excel carregado
    todos_times = sorted(engine.df_pj["TIME"].unique())
    
    target_team = col_audit1.selectbox("Time para Auditar", todos_times)
    contexto = col_audit2.selectbox("Contexto", ["GERAL", "EM CASA (Mandante)", "FORA (Visitante)"])
    
    # Determinar filtros baseados no contexto
    mando_audit = None
    if "CASA" in contexto: mando_audit = "CASA"
    if "FORA" in contexto: mando_audit = "FORA"
    
    if col_audit3.button("Auditar Jogos"):
        # Obter dados brutos
        df_audit_raw = engine.get_meias_stats_raw(data_corte)
        
        # Obter trace
        trace = engine.get_audit_trace(df_audit_raw, window_n, time_filter=target_team, mando_filter=mando_audit)
        
        if not trace.empty:
            st.write(f"**Jogos encontrados na janela ({len(trace)}):**")
            # Formatar para exibição bonita
            trace_show = trace[["DATA", "ADVERSARIO", "MANDO", "PG", "CHUTES", "BASICA"]].copy()
            trace_show["DATA"] = pd.to_datetime(trace_show["DATA"]).dt.strftime("%d/%m/%Y")
            st.dataframe(trace_show, use_container_width=True)
            
            # Médias Calculadas
            avg_pg = trace["PG"].sum() # PG é SOMA não média? Na tabela final é SOMA na janela?
            # Revisando Engine: 
            # "PG": slice_stats["PG"].sum() -> SOMA
            # "CHUTES": slice_stats["CHUTES"].sum() -> SOMA
            # "BASICA": slice_stats["BASICA"].mean() -> MÉDIA
            
            st.markdown("### Totais/Médias Calculados:")
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("PG (Soma)", trace["PG"].sum())
            col_res2.metric("Chutes (Soma)", trace["CHUTES"].sum())
            col_res3.metric("Básica (Média)", round(trace["BASICA"].mean(), 2))
            
            # --- PROVA REAL (Detalhe por Jogador) ---
            st.divider()
            st.markdown("### 🔬 Prova Real (Quem pontuou?)")
            st.info("Abaixo, o detalhe de **cada jogador** que entrou na soma acima. Confira com sua planilha oficial.")
            
            # Filtrar na base bruta apenas os jogos e o time selecionado
            match_ids = trace["MATCH_ID"].tolist()
            df_details = df_audit_raw[
                 (df_audit_raw["MATCH_ID"].isin(match_ids)) & 
                 (df_audit_raw["TIME"] == target_team)
            ].copy()
            
            if not df_details.empty:
                # Selecionar e formatar colunas
                cols_show = ["DATA", "ADVERSARIO", "NOME", "PG", "CHUTES", "BASICA"]
                df_details = df_details[cols_show].sort_values(["DATA", "NOME"])
                df_details["DATA"] = pd.to_datetime(df_details["DATA"]).dt.strftime("%d/%m/%Y")
                
                st.dataframe(df_details, use_container_width=True)
            else:
                st.warning("Não há detalhes de jogadores (estranho, verifique a base).")
        else:
            st.warning("Nenhum jogo encontrado para este time neste contexto/janela.")
