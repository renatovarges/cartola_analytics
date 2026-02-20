import streamlit as st
import pandas as pd
import sys
import os
import tempfile

# Adiciona o diretório raiz ao sys.path para permitir "from src.engine ..."
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine

st.set_page_config(page_title="Cartola Analytics 2026", layout="wide")

# === PROTEÇÃO POR PIN ===
def check_pin():
    """Verifica PIN de acesso usando st.secrets."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    st.markdown("## 🔒 Acesso Restrito")
    st.markdown("Digite o PIN para acessar o sistema.")
    
    pin_input = st.text_input("PIN:", type="password", max_chars=4)
    
    if st.button("Entrar"):
        try:
            correct_pin = st.secrets["pin"]
        except Exception:
            correct_pin = "1979"  # Fallback para desenvolvimento local
        
        if pin_input == str(correct_pin):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ PIN incorreto. Tente novamente.")
    
    return False

if not check_pin():
    st.stop()

st.title("⚽ Cartola Analytics 2026 - Painel de Dados")

from src.rounds import parse_rounds_file
# ... imports anteriores

# Sidebar - Configurações
st.sidebar.header("Parâmetros da Análise")

# 1. Carregar Arquivo de Rodadas
# 1. Carregar Arquivo de Rodadas
# Caminho relativo para funcionar em qualquer PC
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUNDS_FILE = os.path.join(BASE_DIR, "input", "RODADAS_BRASILEIRAO_2026.txt")

rounds_data = {}
if os.path.exists(ROUNDS_FILE):
    rounds_data = parse_rounds_file(ROUNDS_FILE)
    st.sidebar.success(f"Tabela carregada: {len(rounds_data)} rodadas.")
else:
    st.sidebar.error(f"Arquivo de rodadas não encontrado em: {ROUNDS_FILE}")

# 2. Seletor de Rodada Alvo
rodadas_disponiveis = sorted(rounds_data.keys()) if rounds_data else [1]
rodada_alvo = st.sidebar.selectbox("Rodada Alvo", rodadas_disponiveis, index=0)

# 3. Recorte e Filtros
window_n = st.sidebar.number_input("Recorte (N Jogos)", min_value=1, max_value=20, value=5)
tipo_filtro = st.sidebar.radio("Tipo de Filtro", ["TODOS", "POR_MANDO"], index=0, help="TODOS: Últimos N jogos gerais. POR_MANDO: Últimos N jogos em casa (para mandante) ou fora (para visitante).")

# SELETOR DE POSIÇÃO (MACRO)
st.sidebar.markdown("---")
macro_pos = st.sidebar.selectbox("Posição Principal", ["Meias", "Zagueiros", "Goleiros", "Laterais", "Atacantes"], index=0)

# Sub-Filtros (apenas para Meias por enquanto)
mv_filter_val = None
if macro_pos == "Meias":
    mv_selection = st.sidebar.radio("Classificação", ["Todos", "Apenas Meias", "Apenas Volantes"], index=1)
    mv_filter_map = {"Todos": None, "Apenas Meias": "MEIA", "Apenas Volantes": "VOLANTE"}
    mv_filter_val = mv_filter_map[mv_selection]

data_corte = st.sidebar.date_input("Data de Corte", pd.to_datetime("2026-12-31")) # Atualizado padrao pra 2026

# 4. Seleção de Arquivo Excel (Fonte de Dados)
DEFAULT_PATH = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")
IS_LOCAL = os.path.exists(DEFAULT_PATH)

# Opção de upload
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fonte de Dados")

file_path = None
uploaded_file = None

if IS_LOCAL:
    # Modo local: oferece escolha entre arquivo padrão ou upload
    use_upload = st.sidebar.checkbox("Usar planilha personalizada", value=False, 
                                       help="Marque para fazer upload de uma planilha ao invés de usar a padrão")
    if use_upload:
        uploaded_file = st.sidebar.file_uploader(
            "Carregar Excel", 
            type=["xlsx"],
            help="Faça upload da planilha Scouts_Reorganizado.xlsx atualizada"
        )
        if uploaded_file is not None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp.write(uploaded_file.getbuffer())
            tmp.close()
            file_path = tmp.name
            st.sidebar.success(f"✅ Planilha carregada: {uploaded_file.name}")
        else:
            st.sidebar.warning("⚠️ Aguardando upload...")
    else:
        file_path = DEFAULT_PATH
        st.sidebar.info("📁 Usando planilha padrão")
else:
    # Modo nuvem: upload obrigatório
    st.sidebar.info("☁️ Modo Online - Faça upload da planilha atualizada")
    uploaded_file = st.sidebar.file_uploader(
        "Carregar Scouts_Reorganizado.xlsx", 
        type=["xlsx"],
        help="Faça upload da planilha Scouts_Reorganizado.xlsx atualizada para esta rodada"
    )
    if uploaded_file is not None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp.write(uploaded_file.getbuffer())
        tmp.close()
        file_path = tmp.name
        st.sidebar.success(f"✅ Planilha carregada: {uploaded_file.name}")
    else:
        st.sidebar.warning("⚠️ Aguardando upload da planilha...")

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

# Título Principal
st.title(f"Análise de {macro_pos} - Rodada {rodada_alvo}")

# Determinar Confrontos da Lista
confrontos = rounds_data.get(rodada_alvo, [])

if not confrontos:
    st.warning("Nenhum confronto encontrado para esta rodada.")
else:
    st.info(f"Processando {len(confrontos)} jogos da Rodada {rodada_alvo}...")

# Botão para (re)calcular
if st.button(f"Gerar Tabela de {macro_pos}", type="primary"):
    results = []
    progress_bar = st.progress(0)
    
    for i, (mandante, visitante) in enumerate(confrontos):
        try:
            if macro_pos == "Meias":
                 row = engine.generate_confronto_table(
                    mandante, 
                    visitante, 
                    window_n, 
                    data_corte,
                    mando_mode=tipo_filtro,
                    rodada_curr=rodada_alvo,
                    mv_filter=mv_filter_val
                )
            elif macro_pos == "Zagueiros":
                row = engine.generate_zagueiros_table(
                    mandante,
                    visitante,
                    window_n,
                    data_corte,
                    mando_mode=tipo_filtro,
                    rodada_curr=rodada_alvo
                )
            elif macro_pos == "Goleiros":
                row = engine.generate_goleiros_table(
                    mandante,
                    visitante,
                    window_n,
                    data_corte,
                    mando_mode=tipo_filtro,
                    rodada_curr=rodada_alvo
                )
            elif macro_pos == "Laterais":
                row = engine.generate_laterais_table(
                    mandante,
                    visitante,
                    window_n,
                    mando_mode=tipo_filtro
                )
            elif macro_pos == "Atacantes":
                 row = engine.generate_confronto_table(
                    mandante, 
                    visitante, 
                    window_n, 
                    data_corte,
                    mando_mode=tipo_filtro,
                    rodada_curr=rodada_alvo,
                    mv_filter="ATACANTE"
                )
                
            results.append(row)
        except Exception as e:
            st.warning(f"Erro em {mandante}x{visitante}: {e}")
            import traceback
            # print(traceback.format_exc()) # Debug
            
        progress_bar.progress((i + 1) / len(confrontos))

    if results:
        # Salvar no session_state com chave dinamica para nao misturar
        st.session_state["results_key"] = macro_pos
        st.session_state["results_df"] = pd.DataFrame(results)
    else:
        st.warning("Nenhum dado gerado.")

# Lógica de Exibição (Baseado no Estado)
if "results_df" in st.session_state:
    df_results = st.session_state["results_df"]
    current_pos = st.session_state.get("results_key", "Meias")
    
    # Definir Colunas de Exibição Baseado no Tipo
    if current_pos == "Meias" or current_pos == "Atacantes":
        # Ordem Meias
        left_cols = ["COC_AF", "CDF_AF", "COC_CHUTES", "CDF_CHUTES", "COC_PG", "CDF_PG", "COC_BASICA", "CDF_BASICA"]
        center_cols = ["MANDANTE", "VISITANTE"]
        right_cols = ["COF_BASICA", "CDC_BASICA", "COF_PG", "CDC_PG", "COF_CHUTES", "CDC_CHUTES", "COF_AF", "CDC_AF"]
    elif current_pos == "Zagueiros":
        # Ordem Zagueiros: SG, DE, CHUTES, PTS, BASICA
        left_cols = ["COC_SG", "CDF_SG", "COC_DE", "CDF_DE", "COC_CHUTES", "CDF_CHUTES", "COC_PTS", "CDF_PTS", "COC_BASICA", "CDF_BASICA"]
        center_cols = ["MANDANTE", "VISITANTE"]
        right_cols = ["COF_BASICA", "CDC_BASICA", "COF_PTS", "CDC_PTS", "COF_CHUTES", "CDC_CHUTES", "COF_DE", "CDC_DE", "COF_SG", "CDC_SG"]
    elif current_pos == "Goleiros":
        # Ordem Goleiros: AMEAÇAS (ChutAG, ChutPM, Gols) | OPORT (DE, SG, %DE)
        left_cols = ["COC_CHUTES_AG", "CDF_CHUTES_AG", "COC_CHUTES_PM", "CDF_CHUTES_PM", "COC_GOLS", "CDF_GOLS", 
                     "COF_DE", "CDC_DE", "COF_SG", "CDC_SG", "COF_PCT_DE", "CDC_PCT_DE"]
        center_cols = ["MANDANTE", "VISITANTE"]
        right_cols = ["COF_CHUTES_AG", "CDC_CHUTES_AG", "COF_CHUTES_PM", "CDC_CHUTES_PM", "COF_GOLS", "CDC_GOLS",
                      "COC_DE", "CDF_DE", "COC_SG", "CDF_SG", "COC_PCT_DE", "CDF_PCT_DE"]

    elif current_pos == "Laterais":
        # Ordem Laterais (com prefixos corretos)
        left_cols = [
            "COC_LE_DE", "CDF_LE_DE", "COC_LE_PG", "CDF_LE_PG", "COC_LE_BAS", "CDF_LE_BAS",
            "COC_LD_DE", "CDF_LD_DE", "COC_LD_PG", "CDF_LD_PG", "COC_LD_BAS", "CDF_LD_BAS",
            "COC_SG", "CDF_SG"
        ]
        center_cols = ["MANDANTE", "VISITANTE"]
        right_cols = [
            "COF_SG", "CDC_SG",
            "COF_LD_BAS", "CDC_LD_BAS", "COF_LD_PG", "CDC_LD_PG", "COF_LD_DE", "CDC_LD_DE",
            "COF_LE_BAS", "CDC_LE_BAS", "COF_LE_PG", "CDC_LE_PG", "COF_LE_DE", "CDC_LE_DE"
        ]
    else:
        left_cols = []
        center_cols = ["MANDANTE", "VISITANTE"]
        right_cols = []

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
    col_dl1.download_button("Baixar CSV", csv, f"tabela_{current_pos}.csv", "text/csv")
    
    # Botão Gerar PNG
    import matplotlib.pyplot as plt
    from src import renderer_v2 as renderer
    
    if col_dl2.button("📸 Gerar Tabela PNG"):
        with st.spinner("Desenhando tabela em alta resolução..."):
            try:
                # Usa o dataframe ORIGINAL DO RESULTADO
                df_to_render = st.session_state["results_df"]
                
                # Selecionar Renderer Correto
                if current_pos == "Meias":
                    fig = renderer.render_meias_table(df_to_render, rodada_alvo, window_n, tipo_filtro, exibir_legenda=False)
                elif current_pos == "Zagueiros":
                    fig = renderer.render_zagueiros_table(df_to_render, rodada_alvo, window_n, tipo_filtro, exibir_legenda=False)
                elif current_pos == "Goleiros":
                    fig = renderer.render_goleiros_table(df_to_render, rodada_alvo, window_n, tipo_filtro, exibir_legenda=False)
                elif current_pos == "Laterais":
                    fig = renderer.render_laterais_table(df_to_render, rodada_alvo, window_n, tipo_filtro)
                elif current_pos == "Atacantes":
                    fig = renderer.render_atacantes_table(df_to_render, rodada_alvo, window_n, tipo_filtro, exibir_legenda=False)
                else:
                    st.error("Renderer não implementado para esta posição.")
                    fig = None
                
                if fig:
                    from io import BytesIO
                    from PIL import Image as PILImage
                    
                    # === PASSO 1: Renderizar em alta resolução (DPI 600) ===
                    buf_raw = BytesIO()
                    fig.savefig(buf_raw, format="png", dpi=600, bbox_inches='tight', facecolor='white')
                    buf_raw.seek(0)
                    
                    # === PASSO 2: Otimizar para compatibilidade iOS ===
                    # iOS crasha com imagens > ~16.7 megapixels
                    # Limite seguro: 4096px no lado maior, max ~12 MP
                    MAX_SIDE = 4096
                    MAX_MEGAPIXELS = 12.0
                    
                    img = PILImage.open(buf_raw)
                    orig_w, orig_h = img.size
                    orig_mp = (orig_w * orig_h) / 1_000_000
                    
                    needs_resize = False
                    new_w, new_h = orig_w, orig_h
                    
                    # Verificar limite de pixels por lado
                    if max(orig_w, orig_h) > MAX_SIDE:
                        ratio = MAX_SIDE / max(orig_w, orig_h)
                        new_w = int(orig_w * ratio)
                        new_h = int(orig_h * ratio)
                        needs_resize = True
                    
                    # Verificar limite de megapixels
                    new_mp = (new_w * new_h) / 1_000_000
                    if new_mp > MAX_MEGAPIXELS:
                        ratio = (MAX_MEGAPIXELS / new_mp) ** 0.5
                        new_w = int(new_w * ratio)
                        new_h = int(new_h * ratio)
                        needs_resize = True
                    
                    if needs_resize:
                        img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
                    
                    # Salvar PNG otimizado
                    buf = BytesIO()
                    img.save(buf, format="PNG", optimize=True)
                    buf.seek(0)
                    
                    final_size_mb = len(buf.getvalue()) / (1024 * 1024)
                    
                    # Se ainda > 5MB, converter para JPEG de alta qualidade
                    if final_size_mb > 5.0:
                        buf_jpg = BytesIO()
                        if img.mode == 'RGBA':
                            bg = PILImage.new('RGB', img.size, (255, 255, 255))
                            bg.paste(img, mask=img.split()[3])
                            img = bg
                        img.save(buf_jpg, format="JPEG", quality=92, optimize=True)
                        buf_jpg.seek(0)
                        
                        jpg_size_mb = len(buf_jpg.getvalue()) / (1024 * 1024)
                        if jpg_size_mb < final_size_mb:
                            buf = buf_jpg
                            final_size_mb = jpg_size_mb
                            file_ext = "jpg"
                            mime_type = "image/jpeg"
                        else:
                            file_ext = "png"
                            mime_type = "image/png"
                    else:
                        file_ext = "png"
                        mime_type = "image/png"
                    
                    plt.close(fig)
                    
                    # Info para o usuário
                    st.success(f"Imagem otimizada: {new_w}x{new_h}px ({final_size_mb:.1f} MB) - Compatível com iPhone")
                    
                    st.image(buf, caption=f"Tabela {current_pos} Gerada", width="stretch")
                    buf.seek(0)
                    
                    # Download
                    st.download_button(
                        label=f"Baixar Imagem {file_ext.upper()} (Otimizada para Telegram)",
                        data=buf.getvalue(),
                        file_name=f"tabela_{current_pos}_rodada_{rodada_alvo}.{file_ext}",
                        mime=mime_type
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
