import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import pandas as pd
import os
import numpy as np
from . import mapping

# --- CONFIGURAÇÃO VISUAL (PADRÃO TCC) ---
import matplotlib.patheffects as path_effects

COLOR_TCC_GREEN = "#227759"
COLOR_TCC_GREEN_DARK = "#185540" # Faixa superior (Top)
COLOR_TCC_GREEN_MID  = "#40916C" # Faixa média
COLOR_TCC_GREEN_LIGHT = "#95D5B2" # Faixa inferior (ou branco se muito baixo)
COLOR_TCC_PINK  = "#FDE2F3"
COLOR_ROW_EVEN  = "#FFFFFF"
COLOR_ROW_ODD   = "#F8F9FA"  # Leve cinza para diferenciar linhas? Ou manter branco? Usuario nao pediu linhas zebradas. Manter branco.
# COLOR_ROW_ODD = "#FFFFFF"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

def load_image(path):
    if os.path.exists(path):
        return Image.open(path)
    return None

def load_team_image(team_name):
    filename = mapping.get_team_filename(team_name)
    path = os.path.join(ASSETS_DIR, "teams", filename)
    return load_image(path)

def add_image(ax, img, x, y, zoom=0.1, zorder=10):
    """Adiciona imagem usando coordenadas axes fraction (0 a 1)"""
    if img is None: return
    try:
        if not isinstance(img, np.ndarray):
            img = np.array(img.convert('RGBA'))
        ab = AnnotationBbox(
            OffsetImage(img, zoom=zoom, resample=True), 
            (x, y), 
            frameon=False, 
            xycoords='axes fraction',
            zorder=zorder
        )
        ax.add_artist(ab)
    except Exception as e:
        print(f"Erro ao adicionar imagem: {e}")

def render_meias_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False):
    """
    Renderiza tabela de Meias usando matplotlib puro (sem plottable)
    """
    df = df_original.reset_index(drop=True)
    
    # Aumentar altura vertical se tiver legenda
    extra_h = 1.0 if exibir_legenda else 0
    fig, ax = plt.subplots(figsize=(22, len(df) * 1.1 + 7 + extra_h), dpi=400)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    
    # Background
    bg_path = os.path.join(ASSETS_DIR, "logos", "background.png")
    bg_img = load_image(bg_path)
    if bg_img:
        try:
            ax.imshow(bg_img, extent=[0, 1, 0, 1], aspect='auto', zorder=-1, alpha=0.3)
        except:
            fig.patch.set_facecolor("#F5F5F5")
    else:
        fig.patch.set_facecolor("#F5F5F5")
    
    # === CABEÇALHO ===
    header_y = 0.95
    
    logo_path = os.path.join(ASSETS_DIR, "logos", "logo_tcc.png")
    logo_pil = load_image(logo_path)
    if logo_pil:
        add_image(ax, logo_pil, 0.08, header_y, zoom=0.08, zorder=100)
        add_image(ax, logo_pil, 0.92, header_y, zoom=0.08, zorder=100)
    
    # TÍTULO COM EFEITO SUPER-NEGRITO (múltiplas camadas)
    titulo_texto = f"MEIAS - RODADA {rodada_num}"
    # Camadas de fundo para criar espessura extra
    offsets = [(0.0005, 0), (-0.0005, 0), (0, 0.0005), (0, -0.0005),
               (0.0003, 0.0003), (-0.0003, 0.0003), (0.0003, -0.0003), (-0.0003, -0.0003)]
    for dx, dy in offsets:
        ax.text(0.5 + dx, header_y + dy, titulo_texto,
                ha="center", va="center", fontsize=46, fontweight=900,
                color="#0A4D01", transform=ax.transAxes, zorder=99)
    # Camada principal (topo)
    ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight=900,
            color="#0A4D01", transform=ax.transAxes, zorder=100)
    
    filtro_texto = "gerais" if tipo_filtro == "TODOS" else "por mando"
    subtitulo = f"Dados dos últimos {window_n} jogos {filtro_texto}"
    ax.text(0.5, header_y - 0.045, subtitulo,
            ha="center", va="center", fontsize=12, color="black", 
            weight="bold", transform=ax.transAxes, zorder=100)
    
    # === ESTRUTURA DA TABELA ===
    cols_left = ["COC_AF", "CDF_AF", "COC_CHUTES", "CDF_CHUTES", 
                 "COC_PG", "CDF_PG", "COC_BASICA", "CDF_BASICA"]
    cols_center = ["MANDO"]
    cols_right = ["COF_AF", "CDC_AF", "COF_CHUTES", "CDC_CHUTES",
                  "COF_PG", "CDC_PG", "COF_BASICA", "CDC_BASICA"]
    
    all_cols = cols_left + cols_center + cols_right
    col_widths = [0.048] * 8 + [0.12] + [0.048] * 8
    start_x = 0.05
    
    # === SUPER HEADERS ===
    super_header_y = 0.82
    super_header_h = 0.04
    
    groups = [
        ("ASS. FIN.", 0, 2),
        ("CHUTES", 2, 4),
        ("P.G.", 4, 6),
        ("M. BÁSICA", 6, 8),
        ("MANDO", 8, 9),
        ("ASS. FIN.", 9, 11),
        ("CHUTES", 11, 13),
        ("P.G.", 13, 15),
        ("M. BÁSICA", 15, 17),
    ]
    
    for label, start_idx, end_idx in groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        edge_color = "white" if start_idx % 2 == 0 and start_idx > 0 else "none"
        edge_width = 2 if edge_color == "white" else 0
        
        rect = patches.Rectangle(
            (x_start, super_header_y), width, super_header_h,
            facecolor=COLOR_TCC_GREEN, edgecolor=edge_color, linewidth=edge_width,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=13, transform=ax.transAxes, zorder=101)
    
    # === SUB HEADERS - COLADO ===
    sub_header_y = super_header_y - super_header_h  # COLADO
    sub_header_h = 0.04
    COLOR_CINZA = "#E5E7EB"
    
    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA X FORA"  # Texto aqui, UMA vez só
        else:
            prefix = col.split("_")[0]
            bg_color = COLOR_TCC_PINK if prefix in ["COC", "COF"] else COLOR_CINZA
            label = prefix
        
        # Desenhar retângulo SEM BORDAS
        rect = patches.Rectangle(
            (curr_x, sub_header_y), col_widths[i], sub_header_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)
        
        ax.text(curr_x + col_widths[i]/2, sub_header_y + sub_header_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=8 if col == "MANDO" else 13, transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]
    
    # BORDAS DO SUB_HEADER: linhas manuais
    # Top do sub_header
    ax.plot([start_x, start_x + sum(col_widths)], [sub_header_y + sub_header_h, sub_header_y + sub_header_h],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    # Bottom do sub_header (que será o top da primeira linha de dados)
    ax.plot([start_x, start_x + sum(col_widths)], [sub_header_y, sub_header_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    
    # Verticais APENAS entre scouts: 2, 4, 6, 8, 11, 13, 15
    for i in [2, 4, 6, 8, 11, 13, 15]:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [sub_header_y, sub_header_y + sub_header_h],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    


    # === CONFIGURAÇÃO DE CORES (PREMIUM PASTEL V2) ===
    # Ajuste: Tons mais leves e menos "agressivos"
    # Mantendo a Media (#D8F3DC) que o usuário gostou
    
    # Elite: Um verde "Folha" suave, não preto.
    COLOR_ELITE = "#52B788" 
    
    # Bom: Um menta bem claro, ponte entre o Elite e a Media
    COLOR_BOM   = "#95D5B2"
    
    # Media: O tom aprovado
    COLOR_MEDIA = "#D8F3DC"
    
    COLOR_WHITE = "#FFFFFF"

    # === LÓGICA DE REGRAS (FIXA PREVISÍVEL) ===
    # Regras baseadas no número de jogos (N)
    # AF       -> Elite: 10*N | Bom: 7*N | Média: 5*N
    # CHUTES   -> Elite: 8*N  | Bom: 6*N | Média: 5*N
    # PG       -> Elite: 3*N  | Bom: 2*N | Média: 1*N
    # BÁSICA   -> Elite: 3.5  | Bom: 2.5 | Média: 2.0 (Valores fixos pois é Média/Jogo)
    
    def get_color_for_value(col_name, value, n_jogos):
        if value <= 0: return COLOR_ROW_ODD, "black" # Sem destaque
        
        # 1. Definir Limites Base (para N=1)
        if "AF" in col_name:
            lim_elite, lim_bom, lim_media = 10.0, 7.0, 5.0
            is_avg = False
        elif "CHUTES" in col_name:
            lim_elite, lim_bom, lim_media = 8.0, 6.0, 5.0
            is_avg = False
        elif "PG" in col_name:
            lim_elite, lim_bom, lim_media = 3.0, 2.0, 1.0
            is_avg = False
        elif "BASICA" in col_name:
            lim_elite, lim_bom, lim_media = 3.5, 2.5, 2.0
            is_avg = True
        else:
            return COLOR_ROW_ODD, "black"
            
        # 2. Escalar Limites pelo N (apenas se for Soma)
        factor = 1.0 if is_avg else float(n_jogos)
        
        t_elite = lim_elite * factor
        t_bom   = lim_bom * factor
        t_media = lim_media * factor
        
        # 3. Comparar Val >= Threshold
        if value >= t_elite:
            # Elite: Fundo verde médio/forte, Texto branco (ou verde muito escuro para premium?)
            # Vamos testar Branco para contraste clássico com esse verde #52B788
            return COLOR_ELITE, "white"
        elif value >= t_bom:
            # Bom: Fundo verde claro (#95D5B2).
            # Texto Branco pode sumir. Vamos usar um Verde Escuro para ficar elegante ("Tone on Tone")
            return COLOR_BOM, "#081C15" 
        elif value >= t_media:
            # Media: Fundo muito claro (#D8F3DC). Texto Preto ou Verde Escuro.
            return COLOR_MEDIA, "#081C15"
        else:
            return COLOR_ROW_ODD, "black"

    # === LINHAS DE DADOS - COLADAS ===
    row_h = 0.065
    curr_y = sub_header_y
    
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        
        # Alternar cor da linha (Padrão)
        row_color = COLOR_ROW_ODD if idx % 2 != 0 else COLOR_ROW_EVEN
        
        for i, col in enumerate(all_cols):
            val = df.iloc[idx][col] if col != "MANDO" else None
            
            # Definir COR DA CÉLULA
            if col == "MANDO":
                cell_color = COLOR_TCC_GREEN
                text_color = "white"
            else:
                # Usar nova função de cor
                cell_color, text_color = get_color_for_value(col, val, window_n)
                # Se não tem cor de destaque, usa a cor da linha (zebrada)
                if cell_color == COLOR_ROW_ODD:
                    cell_color = row_color
            
            # Desenhar retângulo
            
            # Desenhar retângulo
            rect = patches.Rectangle(
                (curr_x, curr_y), col_widths[i], row_h,
                facecolor=cell_color, edgecolor="none", linewidth=0,
                transform=ax.transAxes, zorder=10
            )
            ax.add_patch(rect)
            
            # Conteúdo
            if col == "MANDO":
                team_casa = df.iloc[idx]["MANDANTE"]
                team_fora = df.iloc[idx]["VISITANTE"]
                
                # 1. SHADOW (Sombra do Escudo)
                # Fica atrás do círculo branco
                circle_radius = 0.020
                aspect_ratio = 22 / (len(df) * 1.1 + 7)
                
                x_casa = curr_x + col_widths[i] * 0.25
                y_casa = curr_y + row_h / 2
                x_fora = curr_x + col_widths[i] * 0.75
                y_fora = curr_y + row_h / 2
                
                # Sombra CASA
                shadow_offset = 0.002 # Pequeno deslocamento
                shadow_casa = patches.Ellipse(
                    (x_casa + shadow_offset, y_casa - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                # Efeito blur na sombra (suavização)
                shadow_casa.set_path_effects([path_effects.withSimplePatchShadow(offset=(0,0), shadow_rgbFace='black', alpha=0.3)])
                ax.add_patch(shadow_casa)

                # CÍRCULO BRANCO + Escudo casa
                img_casa = load_team_image(team_casa)
                
                circle_casa = patches.Ellipse(
                    (x_casa, y_casa), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_casa)
                
                
                # Determinar zoom baseado em palavras-chave (mais robusto)
                zoom_casa = 0.050  # Padrão
                team_casa_lower = str(team_casa).lower()
                if "são paulo" in team_casa_lower or "sao paulo" in team_casa_lower:
                    zoom_casa = 0.040
                elif "flamengo" in team_casa_lower:
                    zoom_casa = 0.040
                elif "athletico" in team_casa_lower or "atlético" in team_casa_lower or "atletico" in team_casa_lower:
                    if "mg" not in team_casa_lower:  # Athletico-PR
                        zoom_casa = 0.040
                elif "atlético-mg" in team_casa_lower or "atletico-mg" in team_casa_lower or "galo" in team_casa_lower:
                    zoom_casa = 0.043
                elif "internacional" in team_casa_lower or "inter" in team_casa_lower:
                    zoom_casa = 0.047
                elif "botafogo" in team_casa_lower:
                    zoom_casa = 0.045
                elif "fluminense" in team_casa_lower:
                    zoom_casa = 0.045
                elif "remo" in team_casa_lower:
                    zoom_casa = 0.045
                
                if img_casa:
                    add_image(ax, img_casa, x_casa, y_casa, zoom=zoom_casa, zorder=200)
                else:
                    ax.text(x_casa, y_casa, str(team_casa)[:3],
                           ha="center", va="center", fontsize=10,
                           color="black", weight="bold", transform=ax.transAxes, zorder=200)
                
                # X central
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h / 2, "×",
                       ha="center", va="center", fontsize=18, color="white", weight="bold",
                       transform=ax.transAxes, zorder=201)
                
                # Sombra FORA
                shadow_fora = patches.Ellipse(
                    (x_fora + shadow_offset, y_fora - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                shadow_fora.set_path_effects([path_effects.withSimplePatchShadow(offset=(0,0), shadow_rgbFace='black', alpha=0.3)])
                ax.add_patch(shadow_fora)

                # CÍRCULO BRANCO + Escudo fora
                img_fora = load_team_image(team_fora)
                
                circle_fora = patches.Ellipse(
                    (x_fora, y_fora), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_fora)
                
                
                # Determinar zoom fora
                zoom_fora = 0.050  # Padrão
                team_fora_lower = str(team_fora).lower()
                if "são paulo" in team_fora_lower or "sao paulo" in team_fora_lower:
                    zoom_fora = 0.040
                elif "flamengo" in team_fora_lower:
                    zoom_fora = 0.040
                elif "athletico" in team_fora_lower or "atlético" in team_fora_lower or "atletico" in team_fora_lower:
                    if "mg" not in team_fora_lower:
                        zoom_fora = 0.040
                elif "atlético-mg" in team_fora_lower or "atletico-mg" in team_fora_lower or "galo" in team_fora_lower:
                    zoom_fora = 0.043
                elif "internacional" in team_fora_lower or "inter" in team_fora_lower:
                    zoom_fora = 0.047
                elif "botafogo" in team_fora_lower:
                    zoom_fora = 0.045
                elif "fluminense" in team_fora_lower:
                    zoom_fora = 0.045 # Faltou fechar este bloco no original então vou manter fechado

                    zoom_fora = 0.045  # Diminuir um pouco
                elif "remo" in team_fora_lower:
                    zoom_fora = 0.045  # Diminuir um pouco
                
                if img_fora:
                    add_image(ax, img_fora, x_fora, y_fora, zoom=zoom_fora, zorder=200)
                else:
                    ax.text(x_fora, y_fora, str(team_fora)[:3],
                           ha="center", va="center", fontsize=10,
                           color="black", weight="bold", transform=ax.transAxes, zorder=200)
            else:
                value = df.iloc[idx].get(col, 0)
                try:
                    val_float = float(value)
                    text = f"{val_float:.1f}" if "BASICA" in col else f"{int(val_float)}"
                except:
                    text = str(value)
                
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, text,
                       ha="center", va="center", fontsize=15, weight="bold",
                       transform=ax.transAxes, zorder=20)
            
            curr_x += col_widths[i]
    
    # === BORDAS DAS CÉLULAS DE DADOS ===
    # Linhas horizontais (bottom de cada linha)
    grid_y = sub_header_y
    for _ in range(len(df)):
        grid_y -= row_h
        ax.plot([start_x, start_x + sum(col_widths)], [grid_y, grid_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
    
    # Linhas verticais APENAS entre scouts
    for i in [2, 4, 6, 8, 11, 13, 15]:
        x_pos = start_x + sum(col_widths[:i])
        # Do topo do sub_header até o bottom da última linha
        ax.plot([x_pos, x_pos], [sub_header_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
    
    # === BORDA VERDE EXTERNA ===
    # Ajustar para começar no topo do super_header (não acima dele)
    border_y_top = super_header_y + super_header_h
    total_height = border_y_top - curr_y
    border_rect = patches.Rectangle(
        (start_x - 0.01, curr_y - 0.01), 
        sum(col_widths) + 0.02, 
        total_height + 0.02,
        facecolor="none", edgecolor=COLOR_TCC_GREEN, linewidth=8,
        transform=ax.transAxes, zorder=5
    )
    ax.add_patch(border_rect)
    
    # Bordas laterais esquerda e direita
    ax.plot([start_x, start_x], [border_y_top, curr_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
    ax.plot([start_x + sum(col_widths), start_x + sum(col_widths)], [border_y_top, curr_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
    
    # === RODAPÉ ===
    footer_h = 0.05
    footer_y = 0.015
    
    footer_rect = patches.Rectangle(
        (0, footer_y), 1, footer_h,
        facecolor=COLOR_TCC_GREEN, edgecolor="none",
        transform=ax.transAxes, zorder=100
    )
    ax.add_patch(footer_rect)
    
    ax.text(0.5, footer_y + footer_h/2, "MATERIAL EXCLUSIVO - TREINANDO CAMPEÕES DE CARTOLA",
            ha="center", va="center", color="white", weight="bold",
            fontsize=18, transform=ax.transAxes, zorder=101)
    
    logo_branco_path = os.path.join(ASSETS_DIR, "logos", "logo_tcc_branco.png")
    logo_branco = load_image(logo_branco_path)
    if logo_branco:
        add_image(ax, logo_branco, 0.08, footer_y + footer_h/2, zoom=0.055, zorder=102)
        add_image(ax, logo_branco, 0.92, footer_y + footer_h/2, zoom=0.055, zorder=102)
    elif logo_pil:
        add_image(ax, logo_pil, 0.08, footer_y + footer_h/2, zoom=0.055, zorder=102)
        add_image(ax, logo_pil, 0.92, footer_y + footer_h/2, zoom=0.055, zorder=102)
    
    
    # === LEGENDA (OPCIONAL) ===
    if exibir_legenda:
        # Posição da legenda: abaixo da borda da tabela, acima do rodapé
        legend_y = curr_y - 0.05
        legend_h = 0.04
        legend_x_start = start_x
        
        # Cores Premium Pastel V2 (Redefinidas aqui para visualização)
        C_ELITE = "#52B788"
        C_BOM   = "#95D5B2"
        C_MEDIA = "#D8F3DC"
        
        # Text alignment colors (Tone on Tone for lighter ones)
        TC_ELITE = "white"
        TC_BOM   = "#081C15"
        TC_MEDIA = "#081C15"
        
        # Itens da legenda (Texto Atualizado)
        items = [
            ("ELITE (Top Player)", C_ELITE, TC_ELITE),
            ("MUITO BOM (Destaque)", C_BOM, TC_BOM), 
            ("ACIMA DA MÉDIA", C_MEDIA, TC_MEDIA)
        ]
        
        item_width = 0.20
        spacing = 0.02
        
        # Label "Legenda:"
        ax.text(legend_x_start, legend_y + legend_h/2, "CRITÉRIOS:", 
               ha="left", va="center", fontsize=12, weight="bold", color="black", 
               transform=ax.transAxes, zorder=50)
        
        curr_legend_x = legend_x_start + 0.08
        
        for text, bg_color, txt_color in items:
            # Retangulo cor
            rect = patches.Rectangle(
                (curr_legend_x, legend_y), item_width, legend_h,
                facecolor=bg_color, edgecolor="black", linewidth=0.5,
                transform=ax.transAxes, zorder=50
            )
            ax.add_patch(rect)
            
            # Texto
            ax.text(curr_legend_x + item_width/2, legend_y + legend_h/2, text,
                   ha="center", va="center", fontsize=10, weight="bold", color=txt_color,
                   transform=ax.transAxes, zorder=51)
            
            curr_legend_x += item_width + spacing

    return fig

# === ZAGUEIROS RENDERER ===
def render_zagueiros_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False):
    """
    Renderiza tabela de ZAGUEIROS 
    """
    df = df_original.reset_index(drop=True)
    
    extra_h = 1.0 if exibir_legenda else 0
    fig, ax = plt.subplots(figsize=(24, len(df) * 1.1 + 7 + extra_h), dpi=400) # Largura um pouco maior pra 5 colunas
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    
    # Background
    bg_path = os.path.join(ASSETS_DIR, "logos", "background.png")
    bg_img = load_image(bg_path)
    if bg_img:
        try:
            ax.imshow(bg_img, extent=[0, 1, 0, 1], aspect='auto', zorder=-1, alpha=0.3)
        except:
            fig.patch.set_facecolor("#F5F5F5")
    else:
        fig.patch.set_facecolor("#F5F5F5")
        
    # === CABEÇALHO ===
    header_y = 0.95
    logo_path = os.path.join(ASSETS_DIR, "logos", "logo_tcc.png")
    logo_pil = load_image(logo_path)
    if logo_pil:
        add_image(ax, logo_pil, 0.08, header_y, zoom=0.08, zorder=100)
        add_image(ax, logo_pil, 0.92, header_y, zoom=0.08, zorder=100)
        
    titulo_texto = f"ZAGUEIROS - RODADA {rodada_num}"
    ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight=1000,
            color="#0A4D01", transform=ax.transAxes, zorder=100)
            
    filtro_texto = "gerais" if tipo_filtro == "TODOS" else "por mando"
    subtitulo = f"Dados dos últimos {window_n} jogos {filtro_texto}"
    ax.text(0.5, header_y - 0.045, subtitulo,
            ha="center", va="center", fontsize=12, color="black", 
            weight="bold", transform=ax.transAxes, zorder=100)
            
    # === ESTRUTURA DA TABELA ZAGUEIROS ===
    # Colunas: SG, DE, CHUTES, PTS, BASICA
    cols_left = ["COC_SG", "CDF_SG", "COC_DE", "CDF_DE", "COC_CHUTES", "CDF_CHUTES", 
                 "COC_PTS", "CDF_PTS", "COC_BASICA", "CDF_BASICA"]
    cols_center = ["MANDO"]
    cols_right = ["COF_SG", "CDC_SG", "COF_DE", "CDC_DE", "COF_CHUTES", "CDC_CHUTES",
                  "COF_PTS", "CDC_PTS", "COF_BASICA", "CDC_BASICA"]
                  
    all_cols = cols_left + cols_center + cols_right

    # Ajuste de larguras (5 blocos de dados de cada lado)
    col_w = 0.040
    col_widths = [col_w] * 10 + [0.12] + [col_w] * 10
    
    # Calcular start_x para centralizar
    total_w = sum(col_widths)
    start_x = (1 - total_w) / 2
    
    # === SUPER HEADERS ===
    super_header_y = 0.82
    super_header_h = 0.04
    
    # Grupos: SG, DE, CHUTES, PONTOS, BASIC
    # Indices na lista col_widths:
    # 0,1 = SG
    # 2,3 = DE
    # 4,5 = CHUTES
    # 6,7 = PTS
    # 8,9 = BASICA
    # 10 = MANDO (Centro)
    # 11,12 = SG
    # 13,14 = DE
    # 15,16 = CHUTES
    # 17,18 = PTS
    # 19,20 = BASICA
    # === SUPER HEADERS ===
    super_header_y = 0.82
    super_header_h = 0.04
    
    # Grupos: SG, DE, CHUTES, PONTOS, BASIC
    # Indices na lista col_widths:
    # 0,1 = SG
    # 2,3 = DE
    # 4,5 = CHUTES
    # 6,7 = PTS
    # 8,9 = BASICA
    # 10 = MANDO (Centro)
    # 11,12 = SG
    # 13,14 = DE
    # 15,16 = CHUTES
    # 17,18 = PTS
    # 19,20 = BASICA
    groups = [
        ("S.G.", 0, 2),
        ("DESARMES", 2, 4),
        ("CHUTES", 4, 6),
        ("PONTOS", 6, 8),
        ("M. BÁSICA", 8, 10),
        ("MANDO", 10, 11),
        ("S.G.", 11, 13),
        ("DESARMES", 13, 15),
        ("CHUTES", 15, 17),
        ("PONTOS", 17, 19),
        ("M. BÁSICA", 19, 21),
    ]
    
    for label, start_idx, end_idx in groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        # Borda branca entre headers (exceto o primeiro e Mando)
        edge_color = "white" if start_idx > 0 and start_idx != 10 else "none"
        edge_width = 2
        
        # Se for lado direito (indice > 10), também precisa de borda branca
        if start_idx > 10:
             edge_color = "white"

        rect = patches.Rectangle(
            (x_start, super_header_y), width, super_header_h,
            facecolor=COLOR_TCC_GREEN, edgecolor=edge_color, linewidth=edge_width,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=11, transform=ax.transAxes, zorder=101)

    # === SUB HEADERS ===
    sub_header_y = super_header_y - super_header_h
    sub_header_h = 0.04
    COLOR_CINZA = "#E5E7EB"
    
    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA X FORA"
        else:
            prefix = col.split("_")[0]
            bg_color = COLOR_TCC_PINK if prefix in ["COC", "COF"] else COLOR_CINZA
            label = prefix
            
        rect = patches.Rectangle(
            (curr_x, sub_header_y), col_widths[i], sub_header_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)
        
        ax.text(curr_x + col_widths[i]/2, sub_header_y + sub_header_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=8 if col == "MANDO" else 11, transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]

    # Bordas Sub Header
    ax.plot([start_x, start_x + sum(col_widths)], [sub_header_y + sub_header_h, sub_header_y + sub_header_h],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    ax.plot([start_x, start_x + sum(col_widths)], [sub_header_y, sub_header_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    
    # Verticais
    vertical_indices = [2, 4, 6, 8, 10, 13, 15, 17, 19]
    for i in vertical_indices:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [sub_header_y, sub_header_y + sub_header_h],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === CORES ZAGUEIROS (PREMIUM PASTEL V2) ===
    COLOR_ELITE = "#52B788" 
    COLOR_BOM   = "#95D5B2"
    COLOR_MEDIA = "#D8F3DC"
    
    def get_color_zag(col_name, value, n_jogos):
        if value <= 0: return COLOR_ROW_ODD, "black"
        
        # Limites BASE (N=1)
        if "SG" in col_name:
            lim_elite, lim_bom, lim_media = 0.8, 0.6, 0.4
            is_avg = False
        elif "DE" in col_name:
             lim_elite, lim_bom, lim_media = 5.0, 3.5, 2.0
             is_avg = False
        elif "CHUTES" in col_name:
             lim_elite, lim_bom, lim_media = 2.0, 1.0, 0.5
             is_avg = False
        elif "PTS" in col_name:
             lim_elite, lim_bom, lim_media = 6.0, 4.0, 2.5
             is_avg = True
        elif "BASICA" in col_name:
             lim_elite, lim_bom, lim_media = 3.0, 2.0, 1.0
             is_avg = True
        else:
            return COLOR_ROW_ODD, "black"
            
        factor = 1.0 if is_avg else float(n_jogos)
        
        if value >= lim_elite * factor: return COLOR_ELITE, "white"
        elif value >= lim_bom * factor : return COLOR_BOM, "#081C15"
        elif value >= lim_media * factor: return COLOR_MEDIA, "#081C15"
        return COLOR_ROW_ODD, "black"

    # === ROWS ===
    row_h = 0.065
    curr_y = sub_header_y
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        row_color = COLOR_ROW_ODD if idx % 2 != 0 else COLOR_ROW_EVEN
        
        for i, col in enumerate(all_cols):
            val = df.iloc[idx][col] if col != "MANDO" else None
            
            if col == "MANDO":
                cell_color = COLOR_TCC_GREEN
                
                # Fundo Verde Central
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=cell_color, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                # "X" central
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, "×",
                       ha="center", va="center", fontsize=18, color="white", weight="bold",
                       transform=ax.transAxes, zorder=201)
                
                # --- VISUAL RICO (Círculo Branco + Sombra + Escudo) ---
                team_casa = df.iloc[idx]["MANDANTE"]
                team_fora = df.iloc[idx]["VISITANTE"]
                
                # Definição de Geometria (Ellipse para manter circularidade independente do Aspect Ratio)
                # Zagueiros width = 24
                fig_width = 24
                fig_height = len(df) * 1.1 + 7 + extra_h
                aspect_ratio = fig_width / fig_height
                
                circle_radius = 0.020 # Unidades do eixo X (0-1)
                
                # MANDANTE (CASA)
                x_casa = curr_x + col_widths[i] * 0.25
                y_casa = curr_y + row_h / 2
                
                # Sombra CASA
                shadow_offset = 0.002
                shadow_casa = patches.Ellipse(
                    (x_casa + shadow_offset, y_casa - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                shadow_casa.set_path_effects([path_effects.withSimplePatchShadow(offset=(0,0), shadow_rgbFace='black', alpha=0.3)])
                ax.add_patch(shadow_casa)

                # Círculo Branco CASA
                circle_casa = patches.Ellipse(
                    (x_casa, y_casa), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_casa)
                
                # Escudo CASA
                img_casa = load_team_image(team_casa)
                # Zoom adjustments (same as Meias logic if needed, or simplfied)
                zoom_casa = 0.050
                t_lower = str(team_casa).lower()
                if "são paulo" in t_lower or "sao paulo" in t_lower or "flamengo" in t_lower: zoom_casa = 0.040
                elif "athletico" in t_lower and "mg" not in t_lower: zoom_casa = 0.040
                
                if img_casa: add_image(ax, img_casa, x_casa, y_casa, zoom=zoom_casa, zorder=200)

                # VISITANTE (FORA)
                x_fora = curr_x + col_widths[i] * 0.75
                y_fora = curr_y + row_h / 2
                
                # Sombra FORA
                shadow_fora = patches.Ellipse(
                    (x_fora + shadow_offset, y_fora - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                shadow_fora.set_path_effects([path_effects.withSimplePatchShadow(offset=(0,0), shadow_rgbFace='black', alpha=0.3)])
                ax.add_patch(shadow_fora)

                # Círculo Branco FORA
                circle_fora = patches.Ellipse(
                    (x_fora, y_fora), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_fora)
                
                # Escudo FORA
                img_fora = load_team_image(team_fora)
                zoom_fora = 0.050
                t_lower = str(team_fora).lower()
                if "são paulo" in t_lower or "sao paulo" in t_lower or "flamengo" in t_lower: zoom_fora = 0.040
                elif "athletico" in t_lower and "mg" not in t_lower: zoom_fora = 0.040
                
                if img_fora: add_image(ax, img_fora, x_fora, y_fora, zoom=zoom_fora, zorder=200)

            else:
                cell_color, text_color = get_color_zag(col, val, window_n)
                if cell_color == COLOR_ROW_ODD: cell_color = row_color
                
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=cell_color, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                if val is not None:
                    if "SG" in col: txt = str(int(val))
                    elif "DE" in col or "CHUTES" in col: txt = f"{int(val)}"
                    else: txt = f"{val:.1f}"
                    
                    ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, txt,
                           ha="center", va="center", fontsize=14, weight="bold", color=text_color,
                           transform=ax.transAxes, zorder=20)
            
            curr_x += col_widths[i]

    # === BORDAS GRID E MOLDURA ===
    grid_y = sub_header_y
    for _ in range(len(df)):
        grid_y -= row_h
        ax.plot([start_x, start_x + sum(col_widths)], [grid_y, grid_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
               
    for i in vertical_indices:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [sub_header_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=15)
               
    border_y_top = super_header_y + super_header_h
    total_height = border_y_top - curr_y
    border_rect = patches.Rectangle(
        (start_x - 0.005, curr_y - 0.005), 
        sum(col_widths) + 0.01, 
        total_height + 0.01,
        facecolor="none", edgecolor=COLOR_TCC_GREEN, linewidth=6,
        transform=ax.transAxes, zorder=5
    )
    ax.add_patch(border_rect)
    
    # Rodapé Corrigido
    footer_h = 0.05
    footer_y = 0.015
    footer_rect = patches.Rectangle((0, footer_y), 1, footer_h, facecolor=COLOR_TCC_GREEN, edgecolor="none", transform=ax.transAxes, zorder=100)
    ax.add_patch(footer_rect)
    ax.text(0.5, footer_y + footer_h/2, "MATERIAL EXCLUSIVO - TREINANDO CAMPEÕES DE CARTOLA", ha="center", va="center", color="white", weight="bold", fontsize=18, transform=ax.transAxes, zorder=101)
    
    logo_branco_path = os.path.join(ASSETS_DIR, "logos", "logo_tcc_branco.png")
    logo_branco = load_image(logo_branco_path)

    if logo_branco:
        add_image(ax, logo_branco, 0.08, footer_y + footer_h/2, zoom=0.055, zorder=102)
        add_image(ax, logo_branco, 0.92, footer_y + footer_h/2, zoom=0.055, zorder=102)

    return fig
