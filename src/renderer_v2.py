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

def render_meias_table(df_original, rodada_num, window_n=5, tipo_filtro="TODOS"):
    """
    Renderiza tabela de Meias usando matplotlib puro (sem plottable)
    """
    df = df_original.reset_index(drop=True)
    
    # Aumentar altura vertical
    fig, ax = plt.subplots(figsize=(22, len(df) * 1.1 + 7), dpi=300)
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
    
    # === CÁLCULO DE QUANTIS (COLORAÇÃO INTELIGENTE RIGOROSA) ===
    # Regras ajustadas para evitar excesso de verde:
    # Verde Escuro: Top 15% (Elite)
    # Verde Médio: Top 30% (Muito Bom)
    # Verde Claro: Top 50% (Acima da Média)
    # Abaixo disso: Branco (Neutro)
    col_quantiles = {}
    for col in all_cols:
        if col == "MANDO": continue
        if col in df.columns:
            try:
                # Se a coluna for só zeros, ignorar
                if df[col].max() <= 0:
                    col_quantiles[col] = (999, 999, 999) # Impossível atingir
                else:
                    q_elite = df[col].quantile(0.85)
                    q_bom   = df[col].quantile(0.70)
                    q_media = df[col].quantile(0.50)
                    col_quantiles[col] = (q_elite, q_bom, q_media)
            except:
                col_quantiles[col] = (999, 999, 999)

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
                # Lógica Rigorosa
                q_elite, q_bom, q_media = col_quantiles.get(col, (999,999,999))
                
                # Só pinta se for positivo
                if val <= 0:
                     cell_color = row_color
                     text_color = "black"
                elif val >= q_elite:
                    cell_color = COLOR_TCC_GREEN_DARK
                    text_color = "white"
                elif val >= q_bom:
                    cell_color = COLOR_TCC_GREEN_MID
                    text_color = "white"
                elif val >= q_media:
                    cell_color = COLOR_TCC_GREEN_LIGHT
                    text_color = "black"
                else:
                    cell_color = row_color # Não pinta (Branco/Cinza)
                    text_color = "black"
            
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
    
    return fig
