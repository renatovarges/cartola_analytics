import streamlit as st
import matplotlib
matplotlib.use('Agg') # Modo servidor (sem GUI)
import pandas as pd
import sys
import os
import tempfile

# Configuração OBRIGATÓRIA no início
st.set_page_config(page_title="Cartola Analytics 2026", layout="wide")

# Adiciona o diretório raiz ao sys.path para permitir "from src.engine ..."
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
from src.caption_goleiros import (
    generate_goalkeeper_caption,
    generate_goalkeeper_caption_plain,
    generate_goalkeeper_caption_for_clipboard,
    generate_goalkeeper_caption_telegram_md,
)
from src.caption_laterais import (
    generate_laterais_caption_plain,
    generate_laterais_caption_telegram_md,
    generate_laterais_caption_html as generate_laterais_caption_html,
)
from src.caption_zagueiros import (
    generate_zagueiros_caption_plain,
    generate_zagueiros_caption_telegram_md,
    generate_zagueiros_caption_html,
)
from src.caption_meias import (
    generate_meias_caption_plain,
    generate_meias_caption_telegram_md,
    generate_meias_caption_html,
)
from src.caption_atacantes import (
    generate_atacantes_caption_plain,
    generate_atacantes_caption_telegram_md,
    generate_atacantes_caption_html,
)
from src.clipboard_utils import copy_text_to_clipboard

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
    
    # Automate AF processing upon load
    with st.sidebar.status("Processando AF Automaticamente...", expanded=True) as status:
        msg = engine.process_af_update()
        if "sucesso" in msg:
            status.update(label="✅ AF Atualizado!", state="complete")
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
                # Enriquecer com perfis calculados pelo motor invisível
                try:
                    _profiles = engine.calculate_goalkeeper_profiles(row)
                    row["PERFIL_MANDANTE"] = _profiles[0]["PERFIL"]
                    row["PERFIL_VISITANTE"] = _profiles[1]["PERFIL"]
                except Exception:
                    row["PERFIL_MANDANTE"] = "-"
                    row["PERFIL_VISITANTE"] = "-"
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
                    import gc
                    
                    # === PASSO 1: Renderizar (DPI já definido no renderer: 200) ===
                    buf_raw = BytesIO()
                    fig.savefig(buf_raw, format="png", dpi=200, bbox_inches='tight', facecolor='white')
                    plt.close(fig)
                    gc.collect()
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


# --- VALIDACAO PERFIS DE GOLEIROS ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Goleiros":
    st.divider()
    with st.expander("Validacao - Perfis de Goleiros", expanded=False):
        st.caption(
            "Tabela de validacao temporaria. Mostra os indices e perfis calculados "
            "para cada goleiro antes de qualquer mudanca no layout visual."
        )
        df_gol_raw = st.session_state["results_df"]
        perfil_rows = []
        for _, row in df_gol_raw.iterrows():
            profiles = engine.calculate_goalkeeper_profiles(row.to_dict())
            for p in profiles:
                p["RODADA"] = rodada_alvo
            perfil_rows.extend(profiles)

        if perfil_rows:
            df_perfil = pd.DataFrame(perfil_rows)
            cols_order = [
                "RODADA", "JOGO", "TIME", "MANDO",
                "SG_INDEX", "PRESSAO_INDEX", "DEFESAS_INDEX", "RISCO_INDEX",
                "CHUTE_PM_CRUZADO", "PERFIL"
            ]
            df_perfil = df_perfil[cols_order]
            st.dataframe(df_perfil, use_container_width=True)

            csv_perfil = df_perfil.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Baixar CSV de Perfis",
                csv_perfil,
                f"perfis_goleiros_rodada_{rodada_alvo}.csv",
                "text/csv",
            )
        else:
            st.info("Nenhum dado de goleiros disponivel para calcular perfis.")

# --- LEGENDA AUTOMÁTICA — MEIAS ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Meias":
    st.divider()
    st.subheader("📋 Legenda automática — Meias")
    st.caption("Destaques por PASSE P/ FINALIZ., FINALIZAÇÕES, G + A e MÉDIA BÁSICA. Cole no Telegram e envie — o negrito aparece automaticamente.")

    try:
        df_mei_cap = st.session_state["results_df"]
        rows_mei   = df_mei_cap.to_dict(orient="records")

        caption_mei_plain = generate_meias_caption_plain(
            rows=rows_mei, rodada=rodada_alvo, window_n=window_n,
        )
        caption_mei_html = generate_meias_caption_html(
            rows=rows_mei, rodada=rodada_alvo, window_n=window_n,
        )
        caption_mei_tg = generate_meias_caption_telegram_md(
            rows=rows_mei, rodada=rodada_alvo, window_n=window_n,
        )

        st.markdown(caption_mei_html, unsafe_allow_html=True)

        col_mei_btn, col_mei_msg = st.columns([1, 3])
        with col_mei_btn:
            if st.button("📋 Copiar para Telegram", key="btn_copy_legenda_mei", type="primary"):
                _ok, _err = copy_text_to_clipboard(caption_mei_tg)
                if _ok:
                    st.session_state["_legenda_mei_copy_status"] = "ok"
                else:
                    st.session_state["_legenda_mei_copy_status"] = _err

        with col_mei_msg:
            _mei_status = st.session_state.get("_legenda_mei_copy_status", "")
            if _mei_status == "ok":
                st.success("✅ Copiado! Cole no Telegram (Ctrl+V) e envie. O negrito aparece na mensagem. 📨")
            elif _mei_status:
                st.warning(f"⚠️ Não foi possível copiar: {_mei_status}")

        with st.expander("📄 Texto puro (alternativa manual)"):
            st.caption("Sem formatação. Use se o botão não funcionar (Ctrl+A → Ctrl+C).")
            st.text_area(
                label="",
                value=caption_mei_plain,
                height=300,
                key="caption_mei_plain_area",
            )

    except Exception as _mei_cap_err:
        st.warning(f"Não foi possível gerar a legenda de meias: {_mei_cap_err}")

# --- LEGENDA AUTOMÁTICA — ATACANTES ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Atacantes":
    st.divider()
    st.subheader("📋 Legenda automática — Atacantes")
    st.caption("Destaques por FINALIZAÇÕES, G + A e MÉDIA BÁSICA. Cole no Telegram e envie — o negrito aparece automaticamente.")

    try:
        df_atk_cap = st.session_state["results_df"]
        rows_atk   = df_atk_cap.to_dict(orient="records")

        caption_atk_plain = generate_atacantes_caption_plain(
            rows=rows_atk, rodada=rodada_alvo, window_n=window_n,
        )
        caption_atk_html = generate_atacantes_caption_html(
            rows=rows_atk, rodada=rodada_alvo, window_n=window_n,
        )
        caption_atk_tg = generate_atacantes_caption_telegram_md(
            rows=rows_atk, rodada=rodada_alvo, window_n=window_n,
        )

        st.markdown(caption_atk_html, unsafe_allow_html=True)

        col_atk_btn, col_atk_msg = st.columns([1, 3])
        with col_atk_btn:
            if st.button("📋 Copiar para Telegram", key="btn_copy_legenda_atk", type="primary"):
                _ok, _err = copy_text_to_clipboard(caption_atk_tg)
                if _ok:
                    st.session_state["_legenda_atk_copy_status"] = "ok"
                else:
                    st.session_state["_legenda_atk_copy_status"] = _err

        with col_atk_msg:
            _atk_status = st.session_state.get("_legenda_atk_copy_status", "")
            if _atk_status == "ok":
                st.success("✅ Copiado! Cole no Telegram (Ctrl+V) e envie. O negrito aparece na mensagem. 📨")
            elif _atk_status:
                st.warning(f"⚠️ Não foi possível copiar: {_atk_status}")

        with st.expander("📄 Texto puro (alternativa manual)"):
            st.caption("Sem formatação. Use se o botão não funcionar (Ctrl+A → Ctrl+C).")
            st.text_area(
                label="",
                value=caption_atk_plain,
                height=300,
                key="caption_atk_plain_area",
            )

    except Exception as _atk_cap_err:
        st.warning(f"Não foi possível gerar a legenda de atacantes: {_atk_cap_err}")

# --- LEGENDA AUTOMÁTICA — GOLEIROS ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Goleiros":
    st.divider()
    st.subheader("📋 Legenda automática — Goleiros")
    st.caption("Apenas perfis positivos (SG+DE, SG, DE). Cole no Telegram e envie — o negrito aparece automaticamente.")

    try:
        df_gol_cap = st.session_state["results_df"]
        rows_cap   = df_gol_cap.to_dict(orient="records")

        # Texto puro — fallback manual
        caption_plain = generate_goalkeeper_caption_plain(
            goleiros_rows=rows_cap,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # HTML para preview visual no app (negrito renderizado)
        from src.caption_goleiros import generate_goalkeeper_caption_html as _gen_html
        caption_html_preview = _gen_html(
            goleiros_rows=rows_cap,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # Telegram Markdown — o que vai para o clipboard
        # **texto** → negrito na mensagem enviada no Telegram
        caption_tg_md = generate_goalkeeper_caption_telegram_md(
            goleiros_rows=rows_cap,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # --- Prévia formatada (HTML no app, para conferir antes de copiar) ---
        _preview = caption_html_preview.replace("\n", "<br>")
        st.markdown(
            f'<div style="background:#f8f9fa;border-radius:8px;padding:16px 20px;'
            f'font-size:15px;line-height:1.8;color:#111;">{_preview}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("&nbsp;", unsafe_allow_html=True)

        # --- Botão de copiar ---
        # Copia texto com marcadores **Telegram Markdown** via clip.exe (Windows nativo).
        # Ao colar no Telegram Desktop e ENVIAR, os ** somem e o negrito aparece.
        col_btn, col_msg = st.columns([1, 3])
        with col_btn:
            if st.button("📋 Copiar para Telegram", key="btn_copy_legenda", type="primary"):
                _ok, _err = copy_text_to_clipboard(caption_tg_md)
                if _ok:
                    st.session_state["_legenda_copy_status"] = "ok"
                else:
                    st.session_state["_legenda_copy_status"] = _err

        with col_msg:
            _status = st.session_state.get("_legenda_copy_status", "")
            if _status == "ok":
                st.success("✅ Copiado! Cole no Telegram (Ctrl+V) e envie. O negrito aparece na mensagem. 📨")
            elif _status:
                st.warning(f"⚠️ Não foi possível copiar: {_status}")

        # --- Fallback: texto puro sempre visível ---
        with st.expander("📄 Texto puro (alternativa manual)"):
            st.caption("Sem formatação. Use se o botão não funcionar (Ctrl+A → Ctrl+C).")
            st.text_area(
                label="",
                value=caption_plain,
                height=260,
                key="caption_plain_area",
            )

    except Exception as _cap_err:
        st.warning(f"Não foi possível gerar a legenda: {_cap_err}")

# --- LEGENDA AUTOMÁTICA — LATERAIS ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Laterais":
    st.divider()
    st.subheader("📋 Legenda automática — Laterais")
    st.caption("Destaques por DESARMES, MÉD. BÁSICA e G + A. Cole no Telegram e envie — o negrito aparece automaticamente.")

    try:
        df_lat_cap = st.session_state["results_df"]
        rows_lat   = df_lat_cap.to_dict(orient="records")

        # Texto puro — fallback manual
        caption_lat_plain = generate_laterais_caption_plain(
            rows=rows_lat,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # HTML para preview visual no app (negrito renderizado)
        caption_lat_html = generate_laterais_caption_html(
            rows=rows_lat,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # Telegram Markdown — o que vai para o clipboard
        caption_lat_tg = generate_laterais_caption_telegram_md(
            rows=rows_lat,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # --- Prévia formatada ---
        _lat_preview = caption_lat_html.replace("\n", "<br>")
        st.markdown(
            f'<div style="background:#f8f9fa;border-radius:8px;padding:16px 20px;'
            f'font-size:15px;line-height:1.8;color:#111;">{_lat_preview}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("&nbsp;", unsafe_allow_html=True)

        # --- Botão de copiar ---
        col_lat_btn, col_lat_msg = st.columns([1, 3])
        with col_lat_btn:
            if st.button("📋 Copiar para Telegram", key="btn_copy_legenda_lat", type="primary"):
                _ok, _err = copy_text_to_clipboard(caption_lat_tg)
                if _ok:
                    st.session_state["_legenda_lat_copy_status"] = "ok"
                else:
                    st.session_state["_legenda_lat_copy_status"] = _err

        with col_lat_msg:
            _lat_status = st.session_state.get("_legenda_lat_copy_status", "")
            if _lat_status == "ok":
                st.success("✅ Copiado! Cole no Telegram (Ctrl+V) e envie. O negrito aparece na mensagem. 📨")
            elif _lat_status:
                st.warning(f"⚠️ Não foi possível copiar: {_lat_status}")

        # --- Fallback: texto puro sempre visível ---
        with st.expander("📄 Texto puro (alternativa manual)"):
            st.caption("Sem formatação. Use se o botão não funcionar (Ctrl+A → Ctrl+C).")
            st.text_area(
                label="",
                value=caption_lat_plain,
                height=300,
                key="caption_lat_plain_area",
            )

    except Exception as _lat_cap_err:
        st.warning(f"Não foi possível gerar a legenda de laterais: {_lat_cap_err}")

# --- LEGENDA AUTOMÁTICA — ZAGUEIROS ---
if "results_df" in st.session_state and st.session_state.get("results_key") == "Zagueiros":
    st.divider()
    st.subheader("📋 Legenda automática — Zagueiros")
    st.caption("Destaques por SG, DESARMES, FINALIZAÇÕES e MÉD. BÁSICA. Cole no Telegram e envie — o negrito aparece automaticamente.")

    try:
        df_zag_cap = st.session_state["results_df"]
        rows_zag   = df_zag_cap.to_dict(orient="records")

        # Texto puro — fallback manual
        caption_zag_plain = generate_zagueiros_caption_plain(
            rows=rows_zag,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # HTML para preview visual no app (negrito renderizado)
        caption_zag_html = generate_zagueiros_caption_html(
            rows=rows_zag,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # Telegram Markdown — o que vai para o clipboard
        caption_zag_tg = generate_zagueiros_caption_telegram_md(
            rows=rows_zag,
            rodada=rodada_alvo,
            window_n=window_n,
        )

        # Preview formatado
        st.markdown(caption_zag_html, unsafe_allow_html=True)

        # --- Botão de copiar ---
        col_zag_btn, col_zag_msg = st.columns([1, 3])
        with col_zag_btn:
            if st.button("📋 Copiar para Telegram", key="btn_copy_legenda_zag", type="primary"):
                _ok, _err = copy_text_to_clipboard(caption_zag_tg)
                if _ok:
                    st.session_state["_legenda_zag_copy_status"] = "ok"
                else:
                    st.session_state["_legenda_zag_copy_status"] = _err

        with col_zag_msg:
            _zag_status = st.session_state.get("_legenda_zag_copy_status", "")
            if _zag_status == "ok":
                st.success("✅ Copiado! Cole no Telegram (Ctrl+V) e envie. O negrito aparece na mensagem. 📨")
            elif _zag_status:
                st.warning(f"⚠️ Não foi possível copiar: {_zag_status}")

        # --- Fallback: texto puro sempre visível ---
        with st.expander("📄 Texto puro (alternativa manual)"):
            st.caption("Sem formatação. Use se o botão não funcionar (Ctrl+A → Ctrl+C).")
            st.text_area(
                label="",
                value=caption_zag_plain,
                height=300,
                key="caption_zag_plain_area",
            )

    except Exception as _zag_cap_err:
        st.warning(f"Não foi possível gerar a legenda de zagueiros: {_zag_cap_err}")

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
