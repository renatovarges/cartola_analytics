
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
            ha="center", va="center", fontsize=46, fontweight=900,
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
                
                # Render Mando Simplificado
                team_casa = df.iloc[idx]["MANDANTE"]
                team_fora = df.iloc[idx]["VISITANTE"]
                
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=cell_color, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)
                
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, "×",
                       ha="center", va="center", fontsize=18, color="white", weight="bold",
                       transform=ax.transAxes, zorder=201)
                
                x_casa = curr_x + col_widths[i] * 0.25
                y_casa = curr_y + row_h / 2
                img_casa = load_team_image(team_casa)
                if img_casa: add_image(ax, img_casa, x_casa, y_casa, zoom=0.045, zorder=200)
                
                x_fora = curr_x + col_widths[i] * 0.75
                y_fora = curr_y + row_h / 2
                img_fora = load_team_image(team_fora)
                if img_fora: add_image(ax, img_fora, x_fora, y_fora, zoom=0.045, zorder=200)

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
    
    # Rodapé
    footer_h = 0.05
    footer_y = 0.015
    footer_rect = patches.Rectangle((0, footer_y), 1, footer_h, facecolor=COLOR_TCC_GREEN, edgecolor="none", transform=ax.transAxes, zorder=100)
    ax.add_patch(footer_rect)
    ax.text(0.5, footer_y + footer_h/2, "ZAGUEIROS - TREINANDO CAMPEÕES", ha="center", va="center", color="white", weight="bold", fontsize=18, transform=ax.transAxes, zorder=101)
    
    if logo_branco:
        add_image(ax, logo_branco, 0.08, footer_y + footer_h/2, zoom=0.055, zorder=102)
        add_image(ax, logo_branco, 0.92, footer_y + footer_h/2, zoom=0.055, zorder=102)

    return fig
