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

def render_meias_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False, title_prefix="MEIAS", position_type="MEIAS"):
    """
    Renderiza tabela de Meias usando matplotlib puro (sem plottable)
    """
    df = df_original.reset_index(drop=True)
    
    # Aumentar altura vertical se tiver legenda
    extra_h = 1.0 if exibir_legenda else 0
    fig, ax = plt.subplots(figsize=(24, len(df) * 1.1 + 7 + extra_h), dpi=600)
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
    # TÍTULO COM EFEITO SUPER-NEGRITO E SOMBRA (Igual Goleiros)
    titulo_texto = f"{title_prefix} - RODADA {rodada_num}"
    
    # Sombra
    ax.text(0.5 + 0.002, header_y - 0.002, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="black", alpha=0.2, transform=ax.transAxes, zorder=99)
            
    # Texto
    txt_obj = ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="#0A4D01", transform=ax.transAxes, zorder=100)
    txt_obj.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#0A4D01")])
    
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

    # === LÓGICA DE REGRAS (PERSONALIZADA USUÁRIO) ===
    # Regras baseadas no número de jogos (N)
    
    def get_color_for_value(col_name, value, n_jogos):
        if value <= 0: return COLOR_ROW_ODD, "black" # Sem destaque
        
        is_avg = False
        
        # 1. Definir Limites Base (POR JOGO)
        # AF: Elite 8/jogo, Bom 6/jogo, Media 4/jogo (?) - (User provided high numbers, implementing literally)
        # CHUTES: Elite 7/jogo, Bom 4/jogo, Media 3/jogo
        # PG: Elite 3/jogo, Bom 2/jogo, Media 1/jogo
        # BÁSICA: Elite 3.5, Bom 2.5, Media 1.5 (Valores fixos média)
        
        if "AF" in col_name:
            if position_type == "ATACANTES":
                lim_elite, lim_bom, lim_media = 6.0, 5.0, 4.0
            else:
                lim_elite, lim_bom, lim_media = 8.0, 6.0, 4.0
        elif "CHUTES" in col_name:
            if position_type == "ATACANTES":
                lim_elite, lim_bom, lim_media = 7.0, 5.0, 4.0
            else:
                lim_elite, lim_bom, lim_media = 7.0, 4.0, 3.0
        elif "PG" in col_name:
            lim_elite, lim_bom, lim_media = 3.0, 2.0, 1.0
        elif "BASICA" in col_name:
            lim_elite, lim_bom, lim_media = 3.5, 2.5, 1.5
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
            # Elite: Fundo verde escuro premium
            return COLOR_ELITE, "white"
        elif value >= t_bom:
            # Bom: Verde médio (#95D5B2)
            return COLOR_BOM, "#081C15" 
        elif value >= t_media:
             # Acima da Média: Verde claro (#D8F3DC)
            return COLOR_MEDIA, "#081C15"
            
        return COLOR_ROW_ODD, "black"

    # === LINHAS DE DADOS - COLADAS ===
    row_h = 0.065
    curr_y = sub_header_y
    
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        
        # Alternar cor da linha (Padrão)
        # Alternar cor da linha (AGORA SEMPRE BRANCO)
        row_color = "white"
        
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
                # Definição de Geometria (Ellipse para manter circularidade independente do Aspect Ratio)
                aspect_ratio = fig.get_figwidth() / fig.get_figheight()
                
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
                       ha="center", va="center", fontsize=13.5, weight="bold",
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
    fig, ax = plt.subplots(figsize=(24, len(df) * 1.1 + 7 + extra_h), dpi=600) # Largura um pouco maior pra 5 colunas
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
    # Efeito SUPER BOLD + SOMBRA no título
    # Sombra
    ax.text(0.5 + 0.002, header_y - 0.002, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="black", alpha=0.2, transform=ax.transAxes, zorder=99)
            
    # Texto
    txt_obj = ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="#0A4D01", transform=ax.transAxes, zorder=100)
    txt_obj.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#0A4D01")])
            
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
        
        # 1. Regra Especial para SG (Depende de N)
        if "SG" in col_name:
            n_int = int(n_jogos)
            # Regras Explicitas do Usuário
            if n_int == 5:
                if value >= 4: return COLOR_ELITE, "white"
                elif value >= 3: return COLOR_BOM, "#081C15"
                elif value >= 2: return COLOR_MEDIA, "#081C15"
            elif n_int == 3:
                if value >= 3: return COLOR_ELITE, "white"
                elif value >= 2: return COLOR_BOM, "#081C15"
                elif value >= 1: return COLOR_MEDIA, "#081C15"
            elif n_int == 2:
                if value >= 2: return COLOR_ELITE, "white"
                elif value >= 1: return COLOR_BOM, "#081C15"
            elif n_int == 1:
                if value >= 1: return COLOR_ELITE, "white"
            else:
                # Fallback para outros N (Proporcional)
                ratio = value / n_jogos
                if ratio >= 0.8: return COLOR_ELITE, "white"     # 80%+
                elif ratio >= 0.6: return COLOR_BOM, "#081C15"   # 60%+
                elif ratio >= 0.4: return COLOR_MEDIA, "#081C15" # 40%+
            
            return COLOR_ROW_ODD, "black"

        # 2. Regras Por Jogo (DE, CHUTES, PTS)
        is_avg = False
        lim_elite, lim_bom, lim_media = 999, 999, 999
        
        if "DE" in col_name:
             # Sugestão: 5, 3, 2
             lim_elite, lim_bom, lim_media = 5.0, 3.0, 2.0
             is_avg = False
        elif "CHUTES" in col_name:
             # Sugestão: 3.0, 2.0, 1.0
             lim_elite, lim_bom, lim_media = 3.0, 2.0, 1.0
             is_avg = False
        elif "PTS" in col_name:
             # Sugestão: 7.0, 5.0, 4.0
             lim_elite, lim_bom, lim_media = 7.0, 5.0, 4.0
             is_avg = True
        elif "BASICA" in col_name:
             # Mantendo padrão Meias para Básica
             lim_elite, lim_bom, lim_media = 3.5, 2.5, 1.5
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
        curr_x = start_x
        row_color = "white" # SEMPRE BRANCO (Padrão V3)
        
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

# === GOLEIROS RENDERER ===
def render_goleiros_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False):
    """
    Renderiza tabela de GOLEIROS (Ameaças vs Oportunidades) 
    """
    df = df_original.reset_index(drop=True)
    
    extra_h = 1.0 if exibir_legenda else 0
    # Tabela mais larga (12 cols por lado vs 10 antes) -> Aumentar width de 24 para 28
    fig, ax = plt.subplots(figsize=(28, len(df) * 1.1 + 7 + extra_h), dpi=600)
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
        
    titulo_texto = f"GOLEIROS - RODADA {rodada_num}"
    
    # Efeito SUPER BOLD + SOMBRA no título
    # Sombra
    txt_shadow = ax.text(0.5 + 0.002, header_y - 0.002, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="black", alpha=0.2, transform=ax.transAxes, zorder=99)
            
    # Texto Principal com Stroke
    txt_obj = ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="#0A4D01", transform=ax.transAxes, zorder=100)
    txt_obj.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#0A4D01")])
            
    filtro_texto = "gerais" if tipo_filtro == "TODOS" else "por mando"
    subtitulo = f"Dados dos últimos {window_n} jogos {filtro_texto}"
    ax.text(0.5, header_y - 0.045, subtitulo,
            ha="center", va="center", fontsize=12, color="black", 
            weight="bold", transform=ax.transAxes, zorder=100)
            
    # === ESTRUTURA DA TABELA GOLEIROS (CORRIGIDO: AMEACAS = ADV / OPORT = TIME) ===
    # Left: Ameaças [COF/CDC] | Oport [COC/CDF]
    cols_left = [
        "COF_CHUTES_AG", "CDC_CHUTES_AG", 
        "COF_CHUTES_PM", "CDC_CHUTES_PM",
        "COF_GOLS", "CDC_GOLS",
        "COC_DE", "CDF_DE",
        "COC_SG", "CDF_SG",
        "COC_PCT_DE", "CDF_PCT_DE"
    ]
    cols_center = ["MANDO"]
    cols_right = [
        "COC_CHUTES_AG", "CDF_CHUTES_AG",
        "COC_CHUTES_PM", "CDF_CHUTES_PM",
        "COC_GOLS", "CDF_GOLS",
        "COF_DE", "CDC_DE",
        "COF_SG", "CDC_SG",
        "COF_PCT_DE", "CDC_PCT_DE"
    ]
                  
    all_cols = cols_left + cols_center + cols_right

    # Ajuste de larguras (12 blocos de dados de cada lado)
    # Total W ideal ~0.9. 24 colunas de dados + 1 centro.
    # 24 * 0.035 = 0.84. Centro 0.10. Total 0.94. Fits.
    col_w = 0.035
    col_widths = [col_w] * 12 + [0.10] + [col_w] * 12
    
    # Calcular start_x para centralizar
    total_w = sum(col_widths)
    start_x = (1 - total_w) / 2
    
    # === SUPER HEADERS (AMEAÇAS / OPORTUNIDADES) ===
    # AJUSTE: Descer tabela para não sobrepor subtitulo
    super_header_y = 0.79 # Era 0.82
    super_header_h = 0.05 # Era 0.04 (Aumentado levemente)
    
    # Grupos Lógicos
    # Indices:
    # 0-6 (3 métricas x 2) = AMEAÇAS
    # 6-12 (3 métricas x 2) = OPORTUNIDADES
    # 12 = MANDO
    # 13-19 = AMEAÇAS (Right)
    # 19-25 = OPORTUNIDADES (Right)
    
    # Mas precisamos de Labels individuais para Sub-headers (CHUT.AG, etc)
    # Vamos desenhar PRIMEIRAMENTE os blocões de AMEAÇAS/OPORTUNIDADES (Azul e Laranja na imagem do user)
    # User Image: Left Side -> AMEAÇAS (Blue) | OPORTUNIDADES (Orange). Right Side -> same.
    
    # Cores Headers Topo
    COLOR_AMEACAS = "#90CAF9" # Azul claro
    COLOR_OPORT   = "#FFCC80" # Laranja claro
    
    top_groups = [
        ("AMEAÇAS", 0, 6, COLOR_AMEACAS),
        ("OPORTUNIDADES", 6, 12, COLOR_OPORT),
        ("AMEAÇAS", 13, 19, COLOR_AMEACAS),
        ("OPORTUNIDADES", 19, 25, COLOR_OPORT)
    ]
    
    # Desenhar Top Level Headers
    top_header_y = super_header_y + 0.05 # Acima do Subheader verde
    top_header_h = 0.045
    
    for label, start_idx, end_idx, color in top_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        rect = patches.Rectangle(
            (x_start, top_header_y), width, top_header_h,
            facecolor=color, edgecolor="white", linewidth=1,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        
        # Sombra Manual Clean (Sem contorno grosso)
        ax.text(x_start + width/2 + 0.001, top_header_y + top_header_h/2 - 0.001, label,
                ha="center", va="center", color="black", weight="bold", alpha=0.25,
                fontsize=13, transform=ax.transAxes, zorder=101)

        # Texto Principal
        txt_header = ax.text(x_start + width/2, top_header_y + top_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=13, transform=ax.transAxes, zorder=102)
                
    # === SUB HEADERS (Verdes: CHUT.AG, CHUT.PM...) ===
    # Agora sim os headers verdes padrão
    
    sub_groups = [
        ("CHUT. AG", 0, 2),
        ("CHUT. PM", 2, 4),
        ("GOLS", 4, 6),
        ("DE", 6, 8),
        ("SG", 8, 10),
        ("% DE", 10, 12),
        
        ("MANDO", 12, 13),
        
        ("CHUT. AG", 13, 15),
        ("CHUT. PM", 15, 17),
        ("GOLS", 17, 19),
        ("DE", 19, 21),
        ("SG", 21, 23),
        ("% DE", 23, 25),
    ]
    
    for label, start_idx, end_idx in sub_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        edge_color = "white"
        
        rect = patches.Rectangle(
            (x_start, super_header_y), width, super_header_h,
            facecolor=COLOR_TCC_GREEN, edgecolor=edge_color, linewidth=1,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=11.5, transform=ax.transAxes, zorder=101) # Aumentado 11->11.5

    # === DATA LABELS (COC/CDF/COF/CDC) ===
    data_labels_h = 0.04
    data_labels_y = super_header_y - data_labels_h
    COLOR_CINZA = "#E5E7EB"
    
    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA • FORA"
            fsize = 9.5
        else:
            prefix = col.split("_")[0] # COC, CDF, COF, CDC
            if prefix in ["COC", "COF"]:
                bg_color = COLOR_TCC_PINK
            else:
                bg_color = COLOR_CINZA
            label = prefix
            fsize = 10.5
            
        rect = patches.Rectangle(
            (curr_x, data_labels_y), col_widths[i], data_labels_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)
        
        ax.text(curr_x + col_widths[i]/2, data_labels_y + data_labels_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=fsize, transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]

    # Bordas Linha Labels
    ax.plot([start_x, start_x + sum(col_widths)], [data_labels_y, data_labels_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
           
    # Verticais Labels
    for i in range(len(col_widths) + 1): # +1 Para fechar a ultima borda
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, data_labels_y + data_labels_h],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === CORES GOLEIROS (PREMIUM) ===
    COLOR_ELITE = "#52B788" 
    COLOR_BOM   = "#95D5B2"
    COLOR_MEDIA = "#D8F3DC"
    
    def get_color_gol(col_name, value, n_jogos):
        # Definições de Cores
        C_ELITE = "#52B788" # Verde Escuro (Elite)
        C_BOM   = "#95D5B2" # Verde Médio (Bom)
        C_CLARO = "#D8F3DC" # Verde Claro
        C_DEFAULT = "white"
        TXT_BLACK = "black" # Texto sempre preto para legibilidade nesses tons claros

        try:
            val = float(value)
        except:
            return C_DEFAULT, TXT_BLACK

        # 1. CHUTES A GOL (AG) ou CHUTES GERAIS
        if "CHUT. AG" in col_name or "_CHUTES_AG" in col_name:
            if val >= 6.0 * n_jogos: return C_ELITE, TXT_BLACK
            elif val >= 5.0 * n_jogos: return C_BOM, TXT_BLACK
            elif val >= 4.0 * n_jogos: return C_CLARO, TXT_BLACK
            return C_DEFAULT, TXT_BLACK

        # 2. CHUTES PM (Para Marcar)
        # Regra: Elite 5, Bom 4, Claro 3
        elif "CHUT. PM" in col_name or "_PM" in col_name:
            if val >= 5.0: return C_ELITE, TXT_BLACK
            elif val >= 4.0: return C_BOM, TXT_BLACK
            elif val >= 3.0: return C_CLARO, TXT_BLACK
            return C_DEFAULT, TXT_BLACK

        # 3. DEFESAS (DE)
        elif "DE" in col_name and "%" not in col_name and "PCT" not in col_name:
            if val >= 5.0 * n_jogos: return C_ELITE, TXT_BLACK
            elif val >= 4.0 * n_jogos: return C_BOM, TXT_BLACK
            elif val >= 3.0 * n_jogos: return C_CLARO, TXT_BLACK
            return C_DEFAULT, TXT_BLACK

        # 4. % DE (% Defesas)
        elif "% DE" in col_name or "PCT_DE" in col_name:
            # Value pode vir como 80.0 ou 0.8? Renderer divide por 100? NÃO, value é bruto.
            # O texto formata com %. Se value for 80, ok. Se for 0.8, *100.
            # Assumindo escala 0-100 baseada no formatação anterior ({:.0f}%).
            # Mas engine calc_pct retorna * 100. Então é 0-100.
            if val >= 80.0: return C_ELITE, TXT_BLACK
            elif val >= 67.0: return C_BOM, TXT_BLACK
            elif val >= 60.0: return C_CLARO, TXT_BLACK
            return C_DEFAULT, TXT_BLACK

        # 5. GOLS (Inverso - Menor é melhor)
        elif "GOLS" in col_name:
            # Regras por Janela
            if n_jogos >= 5:
                if val <= 1: return C_ELITE, TXT_BLACK
                elif val <= 2: return C_BOM, TXT_BLACK
                elif val <= 3: return C_CLARO, TXT_BLACK
            elif n_jogos >= 3:
                # Elite 0, Med 1, Claro 2
                if val <= 0: return C_ELITE, TXT_BLACK
                elif val <= 1: return C_BOM, TXT_BLACK
                elif val <= 2: return C_CLARO, TXT_BLACK
            elif n_jogos == 2:
                # Elite 0, Med 1
                if val <= 0: return C_ELITE, TXT_BLACK
                elif val <= 1: return C_BOM, TXT_BLACK
            elif n_jogos == 1:
                # Elite 0
                if val <= 0: return C_ELITE, TXT_BLACK
            
            return C_DEFAULT, TXT_BLACK

        # 6. SG (Clean Sheets)
        elif "SG" in col_name:
            if n_jogos >= 5:
                if val >= 4: return C_ELITE, TXT_BLACK
                elif val >= 3: return C_BOM, TXT_BLACK
                elif val >= 2: return C_CLARO, TXT_BLACK
            elif n_jogos >= 3:
                # 3 Elite, 2 Bom, 1 Claro
                if val >= 3: return C_ELITE, TXT_BLACK
                elif val >= 2: return C_BOM, TXT_BLACK
                elif val >= 1: return C_CLARO, TXT_BLACK
            elif n_jogos == 2:
                # 2 Elite, 1 Bom
                if val >= 2: return C_ELITE, TXT_BLACK
                elif val >= 1: return C_BOM, TXT_BLACK
            elif n_jogos == 1:
                # 1 Elite
                if val >= 1: return C_ELITE, TXT_BLACK
                
            return C_DEFAULT, TXT_BLACK
        
        return C_DEFAULT, TXT_BLACK
        
        
    # === ROWS ===
    row_h = 0.065
    curr_y = data_labels_y
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        row_color = "white" # REMOVIDO ZEBRADO: Sempre Branco
        
        for i, col in enumerate(all_cols):
            val = df.iloc[idx][col] if col != "MANDO" else None
            
            if col == "MANDO":
                # MANDO CELL (Same as V2)
                cell_color = COLOR_TCC_GREEN
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=cell_color, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, "×",
                       ha="center", va="center", fontsize=20, color="white", weight="bold",
                       transform=ax.transAxes, zorder=201)
                
                # --- VISUAL RICO MANDO (Igual Zagueiros) ---
                team_casa = df.iloc[idx]["MANDANTE"]
                team_fora = df.iloc[idx]["VISITANTE"]
                
                # Aspect Ratio Adjust
                fig_width = 28
                fig_height = len(df) * 1.1 + 7 + extra_h
                aspect_ratio = fig_width / fig_height
                
                # Aumentar Raio para caber
                circle_radius = 0.016 
                
                # Casa
                x_casa = curr_x + col_widths[i] * 0.25
                y_casa = curr_y + row_h / 2
                
                # 1. Sombra
                shadow_offset = 0.002
                shadow_casa = patches.Ellipse(
                    (x_casa + shadow_offset, y_casa - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                ax.add_patch(shadow_casa)
                
                # 2. Círculo Branco
                circle_casa = patches.Ellipse(
                    (x_casa, y_casa), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_casa)
                
                # 3. Logo (Zoom Dinamico)
                zoom_casa = 0.045 # Aumentar zoom base (de 0.035 para 0.045)
                # (Lógica simplificada de zoom, ou copiar completa se precisar)
                
                logo_c = load_team_image(team_casa)
                if logo_c: add_image(ax, logo_c, x_casa, y_casa, zoom=zoom_casa, zorder=200)
                
                # Fora
                x_fora = curr_x + col_widths[i] * 0.75
                y_fora = y_casa
                
                # 1. Sombra
                shadow_fora = patches.Ellipse(
                    (x_fora + shadow_offset, y_fora - shadow_offset), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="black", edgecolor="none", alpha=0.3,
                    transform=ax.transAxes, zorder=198
                )
                ax.add_patch(shadow_fora)
                
                # 2. Círculo Branco
                circle_fora = patches.Ellipse(
                    (x_fora, y_fora), 
                    width=circle_radius * 2, 
                    height=circle_radius * 2 * aspect_ratio,
                    facecolor="white", edgecolor="none",
                    transform=ax.transAxes, zorder=199
                )
                ax.add_patch(circle_fora)
                
                logo_f = load_team_image(team_fora)
                if logo_f: add_image(ax, logo_f, x_fora, y_fora, zoom=zoom_casa, zorder=200)

            else:
                # DADOS CELL
                if "PM" in col: fmt = "{:.1f}"
                elif "PCT" in col: fmt = "{:.0f}%"
                elif "GOLS" in col or "DE" in col or "SG" in col or "CHUTES" in col: 
                    fmt = "{:.0f}"
                else: fmt = "{:.1f}"
                
                txt = fmt.format(val)
                
                # Cor (Placeholder Function)
                bg_c, txt_c = get_color_gol(col, val, window_n)
                
                # Alternar linha
                if bg_c == COLOR_ROW_ODD or bg_c == COLOR_ROW_EVEN:
                   bg_c = row_color
                
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=bg_c, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, txt,
                       ha="center", va="center", color=txt_c, weight="bold",
                       fontsize=13.5, transform=ax.transAxes, zorder=15) # Aumentado 12->13.5
                       
            curr_x += col_widths[i]
            
        # Linha separadora row
        ax.plot([start_x, start_x + sum(col_widths)], [curr_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51) # Escurecido de E5E7EB para black
               
    # === BORDAS GRID E MOLDURA (Recalcular height) ===
    # (Copiar lógica de borda final)
    grid_y = data_labels_y
    for _ in range(len(df)):
        grid_y -= row_h
    
    # Verticais Grid de Dados (Apenas entre grupos de Scouts)
    # Zagueiros: Pares 2 cols. Indices: 2, 4, 6, 8, 10, 11(Mando Start), 12(Mando End), 14, 16, 18, 20, 22
    # Cols: SG(2), DE(2), CHUTES(2), PTS(2), BASICA(2) -> 10 Left.
    # MANDO -> 11.
    # Right -> 10.
    # Indices: 2, 4, 6, 8, 10, 11, 12, 14, 16, 18, 20, 22
    
    gol_vert_indices = [2, 4, 6, 8, 10, 12, 13, 15, 17, 19, 21, 23]
    
    for i in gol_vert_indices:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=202)
    
    border_y_top = top_header_y + top_header_h # Top absoluto
    total_height = border_y_top - curr_y
    border_rect = patches.Rectangle(
        (start_x - 0.005, curr_y - 0.005), 
        sum(col_widths) + 0.01, 
        total_height + 0.01,
        facecolor="none", edgecolor=COLOR_TCC_GREEN, linewidth=6,
        transform=ax.transAxes, zorder=5
    )
    ax.add_patch(border_rect)
    
    # Rodapé
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

# === LATERAIS RENDERER ===
def render_laterais_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False):
    """
    Renderiza tabela de LATERAIS (LE/LD)
    Estrutura: 
    Left: [LE: DE, PG, Bas] [LD: DE, PG, Bas] [SG]
    Center: [MANDO]
    Right: [SG] [LD: Bas, PG, DE] [LE: Bas, PG, DE]
    Total: 6+6+2 = 14 * 2 + 1 = 29 Colunas.
    """
    df = df_original.reset_index(drop=True)
    
    extra_h = 1.0 if exibir_legenda else 0
    # Tabela MUITO larga (29 cols). Goleiros era 25 e width 28.
    # 29/25 * 28 ~ 32.5. Vamos usar width=34 para garantir.
    fig, ax = plt.subplots(figsize=(34, len(df) * 1.1 + 7 + extra_h), dpi=600)
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
        
    titulo_texto = f"LATERAIS - RODADA {rodada_num}"
    
    # Sombra
    ax.text(0.5 + 0.002, header_y - 0.002, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="black", alpha=0.2, transform=ax.transAxes, zorder=99)
            
    # Texto Principal
    txt_obj = ax.text(0.5, header_y, titulo_texto,
            ha="center", va="center", fontsize=46, fontweight="bold",
            color="#0A4D01", transform=ax.transAxes, zorder=100)
    txt_obj.set_path_effects([path_effects.withStroke(linewidth=3, foreground="#0A4D01")])
            
    filtro_texto = "gerais" if tipo_filtro == "TODOS" else "por mando"
    subtitulo = f"Dados dos últimos {window_n} jogos {filtro_texto}"
    ax.text(0.5, header_y - 0.045, subtitulo,
            ha="center", va="center", fontsize=12, color="black", 
            weight="bold", transform=ax.transAxes, zorder=100)
            
    # === ESTRUTURA DE COLUNAS ===
    # Left Side
    # LE: DE, PG, BAS
    cols_le_left = ["COC_LE_DE", "CDF_LE_DE", "COC_LE_PG", "CDF_LE_PG", "COC_LE_BAS", "CDF_LE_BAS"]
    # LD: DE, PG, BAS
    cols_ld_left = ["COC_LD_DE", "CDF_LD_DE", "COC_LD_PG", "CDF_LD_PG", "COC_LD_BAS", "CDF_LD_BAS"]
    # SG
    cols_sg_left = ["COC_SG", "CDF_SG"]
    
    cols_center = ["MANDO"]
    
    # Right Side (Reverso)
    # SG
    cols_sg_right = ["COF_SG", "CDC_SG"] # Mantem ordem COC/CDF ou COF/CDC interno? Sim, COF=Pro, CDC=Contra.
    # LD: BAS, PG, DE (Inverso da Esquerda)
    cols_ld_right = ["COF_LD_BAS", "CDC_LD_BAS", "COF_LD_PG", "CDC_LD_PG", "COF_LD_DE", "CDC_LD_DE"]
    # LE: BAS, PG, DE
    cols_le_right = ["COF_LE_BAS", "CDC_LE_BAS", "COF_LE_PG", "CDC_LE_PG", "COF_LE_DE", "CDC_LE_DE"]
    
    all_cols = (cols_le_left + cols_ld_left + cols_sg_left + 
                cols_center + 
                cols_sg_right + cols_ld_right + cols_le_right)
                
    # Larguras
    # 28 colunas de dados + 1 centro = 29.
    # Total W ideal 0.94.
    # 0.94 - 0.10 (centro) = 0.84
    # 0.84 / 28 = 0.030.
    col_w = 0.030
    col_widths = [col_w] * 14 + [0.10] + [col_w] * 14
    
    total_w = sum(col_widths)
    start_x = (1 - total_w) / 2
    
    # === SUPER HEADERS (LE / LD / SG) ===
    super_header_y = 0.79
    super_header_h = 0.05
    
    # Cores Grupos
    C_LE_TOP = "#4FC3F7" # Azul LE
    C_LD_TOP = "#FFB74D" # Laranja LD
    C_SG_TOP = "#81C784" # Verde SG
    
    # Grupos Topo
    # Indices relativos ao inicio
    # Left: 0-6 (LE), 6-12 (LD), 12-14 (SG)
    # Right: 15-17 (SG), 17-23 (LD), 23-29 (LE)
    
    top_groups = [
        ("LATERAL ESQUERDO", 0, 6, C_LE_TOP),
        ("LATERAL DIREITO", 6, 12, C_LD_TOP),
        ("DEFESA", 12, 14, C_SG_TOP),
        
        ("DEFESA", 15, 17, C_SG_TOP),
        ("LATERAL DIREITO", 17, 23, C_LD_TOP),
        ("LATERAL ESQUERDO", 23, 29, C_LE_TOP)
    ]
    
    top_header_y = super_header_y + 0.05
    top_header_h = 0.045
    
    for label, start_idx, end_idx, color in top_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        rect = patches.Rectangle(
            (x_start, top_header_y), width, top_header_h,
            facecolor=color, edgecolor="white", linewidth=1,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        
        # Sombra removida por feedback do usuário
        # ax.text(x_start + width/2 + 0.0003, top_header_y + top_header_h/2 - 0.0003, label,
        #         ha="center", va="center", color="black", weight="bold", alpha=0.15,
        #         fontsize=13, transform=ax.transAxes, zorder=101)
                
        # Texto
        ax.text(x_start + width/2, top_header_y + top_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=15, transform=ax.transAxes, zorder=102)

    # === SUB HEADERS (Verdes: DE, PG, BAS...) ===
    # Left: [DE, DE] [PG, PG] [BAS, BAS] ...
    # Right is reversed instructions
    
    sub_groups = [
        # Left LE
        ("DESARMES", 0, 2), ("G + A", 2, 4), ("M. BÁSICA", 4, 6),
        # Left LD
        ("DESARMES", 6, 8), ("G + A", 8, 10), ("M. BÁSICA", 10, 12),
        # Left SG
        ("SG", 12, 14),
        
        ("MANDO", 14, 15),
        
        # Right SG
        ("SG", 15, 17),
        # Right LD (Reverse: MED, PG, DE)
        ("M. BÁSICA", 17, 19), ("G + A", 19, 21), ("DESARMES", 21, 23),
        # Right LE (Reverse: MED, PG, DE)
        ("M. BÁSICA", 23, 25), ("G + A", 25, 27), ("DESARMES", 27, 29),
    ]
    
    for label, start_idx, end_idx in sub_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        rect = patches.Rectangle(
            (x_start, super_header_y), width, super_header_h,
            facecolor=COLOR_TCC_GREEN, edgecolor="white", linewidth=1,
            transform=ax.transAxes, zorder=100
        )
        ax.add_patch(rect)
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold", 
                fontsize=12.5, transform=ax.transAxes, zorder=101) # Fonte menor p/ caber

    # === DATA LABELS (COC/CDF...) ===
    data_labels_h = 0.04
    data_labels_y = super_header_y - data_labels_h
    COLOR_CINZA = "#E5E7EB"
    
    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            # Label especial MANDO (CASA . FORA)
            label = "CASA • FORA"
            bg_color = "white"
            fsize=9
        else:
            # Prefix Logic
            prefix = col.split("_")[0] # COC, CDF, COF, CDC
            if prefix in ["COC", "COF"]:
                bg_color = COLOR_TCC_PINK
            else:
                bg_color = COLOR_CINZA
            label = prefix
            fsize=12
            
        rect = patches.Rectangle(
            (curr_x, data_labels_y), col_widths[i], data_labels_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)
        ax.text(curr_x + col_widths[i]/2, data_labels_y + data_labels_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=fsize, transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]

    # Bordas Labels
    ax.plot([start_x, start_x + sum(col_widths)], [data_labels_y, data_labels_y], color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    
    for i in range(len(col_widths)+1):
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, data_labels_y + data_labels_h], color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === CORES LATERAIS (PLACEHOLDER) ===
    def get_color_lat(col_name, value, n_jogos):
        C_ELITE = "#52B788"
        C_BOM   = "#95D5B2"
        C_CLARO = "#D8F3DC"
        C_DEFAULT = "white"
        TXT = "black"
        
        try: val = float(value)
        except: return C_DEFAULT, TXT
        
        # Logica preliminar (User vai refinar)
        # DE (Desarmes)
        if "_DE" in col_name and "PCT" not in col_name:
            if val >= 4: return C_ELITE, TXT
            elif val >= 3: return C_BOM, TXT
            elif val >= 2: return C_CLARO, TXT
            
        # PG (Gols + Ass)
        elif "_PG" in col_name:
            if val >= 1: return C_ELITE, TXT # 1 gol/ass é mto bom p lateral
            
        # BAS (Basica)
        elif "_BAS" in col_name:
             if val >= 4.0: return C_ELITE, TXT
             elif val >= 3.0: return C_BOM, TXT
             elif val >= 2.0: return C_CLARO, TXT
             
        # SG
        elif "_SG" in col_name:
             if n_jogos >= 5 and val >= 3: return C_ELITE, TXT
             if n_jogos >= 5 and val >= 2: return C_BOM, TXT
             
        return C_DEFAULT, TXT

    # === ROWS ===
    row_h = 0.065
    curr_y = data_labels_y
    
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        
        for i, col in enumerate(all_cols):
            val = df.iloc[idx][col] if col != "MANDO" else None
            
            if col == "MANDO":
                # Render Mando (Igual Goleiros/V2)
                cell_color = COLOR_TCC_GREEN
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=cell_color, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, "×",
                       ha="center", va="center", fontsize=20, color="white", weight="bold",
                       transform=ax.transAxes, zorder=201)
                       
                # Logos Mando (Copiar logica V2 - Code Reuse idealmente, mas aqui duplico para segurança)
                team_casa = df.iloc[idx]["MANDANTE"]
                team_fora = df.iloc[idx]["VISITANTE"]
                
                # Aspect calc
                fig_width = 34
                fig_height = len(df) * 1.1 + 7 + extra_h
                aspect = fig_width / fig_height
                radius = 0.014 # Ajuste leve pois tabela é mais larga
                
                # Casa
                xc = curr_x + col_widths[i]*0.25
                yc = curr_y + row_h/2
                
                # Sombra
                sh_off = 0.0015
                ax.add_patch(patches.Ellipse((xc+sh_off, yc-sh_off), radius*2, radius*2*aspect, facecolor="black", alpha=0.3, transform=ax.transAxes, zorder=198))
                ax.add_patch(patches.Ellipse((xc, yc), radius*2, radius*2*aspect, facecolor="white", transform=ax.transAxes, zorder=199))
                
                # Logic for logo zoom
                def get_logo_zoom(t_name):
                    # Exceções (Mantém tamanho original ou leve ajuste)
                    # "São Paulo", "Flamengo", "Athlético-PR"
                    t_upper = t_name.upper()
                    exceptions = ["FLAMENGO", "SÃO PAULO", "SAO PAULO", "ATHLETICO", "PARANAENSE", "CAP"]
                    for exc in exceptions:
                        if exc in t_upper:
                            return 0.040 # Tamanho padrão
                    # Aumentar para os demais
                    return 0.052

                lc = load_team_image(team_casa)
                if lc: 
                    z_c = get_logo_zoom(team_casa)
                    add_image(ax, lc, xc, yc, zoom=z_c, zorder=200)
                
                # Fora
                xf = curr_x + col_widths[i]*0.75
                yf = yc
                ax.add_patch(patches.Ellipse((xf+sh_off, yf-sh_off), radius*2, radius*2*aspect, facecolor="black", alpha=0.3, transform=ax.transAxes, zorder=198))
                ax.add_patch(patches.Ellipse((xf, yf), radius*2, radius*2*aspect, facecolor="white", transform=ax.transAxes, zorder=199))
                
                lf = load_team_image(team_fora)
                if lf: 
                    z_f = get_logo_zoom(team_fora)
                    add_image(ax, lf, xf, yf, zoom=z_f, zorder=200)
                
            else:
                # Dados
                fmt = "{:.1f}"
                if "_DE" in col or "_PG" in col or "_SG" in col: fmt = "{:.0f}"
                
                txt = fmt.format(val) if isinstance(val, (int, float)) else str(val)
                
                bg_c, txt_c = get_color_lat(col, val, window_n)
                
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=bg_c, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, txt,
                        ha="center", va="center", color=txt_c, weight="bold",
                        fontsize=16, transform=ax.transAxes, zorder=15)
                        
            curr_x += col_widths[i]
            
        # Linha Horizontal Row
        ax.plot([start_x, start_x + sum(col_widths)], [curr_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === VERTICAIS (Separar Grupos) ===
    # 0, 2, 4, 6(Grupo), 8, 10, 12(Grupo), 14(Grupo Mando Start)...
    # Indices:
    # LE: 2, 4, 6(End)
    # LD: 8, 10, 12(End)
    # SG: 14(End)
    # MANDO: 15(End)
    # SG Right: 17(End)
    # LD Right: 19, 21, 23(End)
    # LE Right: 25, 27, 29(End)
    
    vert_indices = [2, 4, 6, 8, 10, 12, 14, 15, 17, 19, 21, 23, 25, 27, 29]
    for i in vert_indices:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=202)
               
    # Borda Externa
    border_y_top = top_header_y + top_header_h
    total_height = border_y_top - curr_y
    border_rect = patches.Rectangle(
        (start_x - 0.005, curr_y - 0.005), 
        sum(col_widths) + 0.01, 
        total_height + 0.01,
        facecolor="none", edgecolor=COLOR_TCC_GREEN, linewidth=6,
        transform=ax.transAxes, zorder=5
    )
    ax.add_patch(border_rect)
    
    # Rodapé
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

def render_atacantes_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS", exibir_legenda=False):
    """
    Renderiza tabela de Atacantes usando o mesmo layout de Meias.
    """
    return render_meias_table(df_original, rodada_num, window_n, tipo_filtro, exibir_legenda, title_prefix="ATACANTES", position_type="ATACANTES")
