import math
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
import matplotlib.colors as mcolors

COLOR_TCC_GREEN = "#227759"
COLOR_TCC_GREEN_DARK = "#185540" # Faixa superior (Top)
COLOR_TCC_GREEN_MID  = "#40916C" # Faixa média
COLOR_TCC_GREEN_LIGHT = "#95D5B2" # Faixa inferior (ou branco se muito baixo)
COLOR_TCC_PINK  = "#FDE2F3"
COLOR_ROW_EVEN  = "#FFFFFF"
COLOR_ROW_ODD   = "#F8F9FA"  # Leve cinza para diferenciar linhas? Ou manter branco? Usuario nao pediu linhas zebradas. Manter branco.
# COLOR_ROW_ODD = "#FFFFFF"

# === CORES GERAIS (PREMIUM PASTEL V2) ===
COLOR_ELITE = "#52B788" 
COLOR_BOM   = "#95D5B2"
COLOR_MEDIA = "#D8F3DC"
COLOR_CLARO = "#D8F3DC"
COLOR_DEFAULT = "white"

# === LABELS DOS SUBTÍTULOS (substituem COC/CDF/COF/CDC visualmente) ===
PREFIX_LABELS = {
    "COC": "CONQ.\nPELO\nMANDANTE",
    "CDF": "CEDIDO\nPELO\nVISITANTE",
    "COF": "CONQ.\nPELO\nVISITANTE",
    "CDC": "CEDIDO\nPELO\nMANDANTE",
}

# === TEXTO VISUAL DOS PERFIS DE GOLEIRO ===
# Texto exibido na tabela (interno continua SG+DE/SG/DE/BOMB/-)
PERFIL_DISPLAY = {
    "SG+DE": "SG+\nDEFESAS",
    "SG":    "SG",
    "DE":    "DEFESAS",
    "BOMB":  "ALTO\nRISCO",
    "-":     "—",
}

# Cores neutras (sem verde) para as células de PERFIL
PERFIL_BG_COLORS = {
    "SG+DE": "#93C5FD",  # azul claro evidente  (blue-300) — mais completo
    "SG":    "#DBEAFE",  # azul muito claro (blue-100)
    "DE":    "#E5E7EB",  # cinza azulado neutro — mais discreto que SG+DE
    "BOMB":  "#FECACA",  # vermelho/salmão claro (red-200)
    "-":     "#F3F4F6",  # cinza muito claro
}

# Grafite para o cabeçalho PERFIL
COLOR_PERFIL_HEADER = "#374151"

# === PREMIUM GRADIENT COLORS (top=claro → bottom=escuro) ===
GRAD_PRESSAO   = ("#64B5F6", "#0D47A1")   # azul claro  → azul profundo
GRAD_RISCO     = ("#E57373", "#B71C1C")   # vermelho claro → vermelho escuro
GRAD_POTENCIAL = ("#FFB74D", "#BF360C")   # laranja claro  → laranja profundo
GRAD_PERFIS    = ("#90A4AE", "#263238")   # cinza azulado  → grafite escuro
GRAD_SCOUTS    = ("#43A047", "#1A3E22")   # verde médio    → verde escuro premium


def draw_gradient_rect(ax, x, y, w, h, color_top, color_bottom, n_steps=20, zorder=100):
    """Retângulo com gradiente vertical (topo claro → base escura) usando N tiras."""
    c1 = np.array(mcolors.to_rgb(color_top))    # topo
    c2 = np.array(mcolors.to_rgb(color_bottom))  # base
    step_h = h / n_steps
    for i in range(n_steps):
        t = i / max(n_steps - 1, 1)  # 0 = base, 1 = topo
        c = c2 * (1.0 - t) + c1 * t
        ax.add_patch(patches.Rectangle(
            (x, y + i * step_h), w, step_h + 0.0002,
            facecolor=tuple(np.clip(c, 0, 1)), edgecolor="none",
            transform=ax.transAxes, zorder=zorder
        ))

# === HELPER UNIFICADO SG ===
def get_sg_color(val, n_jogos):
    n = int(n_jogos)
    # Regras do Usuário
    # 5 jogos: 4+ Elite, 3 Bom, 2 Médio
    # 4 jogos: 4+ Elite, 3 Bom, 2 Médio
    # 3 jogos: 3+ Elite, 2 Bom, 1 Médio
    # 2 jogos: 2+ Elite, 1 Bom
    # 1 jogo:  1+ Elite
    
    # Elite
    if n == 5 and val >= 4: return COLOR_ELITE, "white"
    if n == 4 and val >= 4: return COLOR_ELITE, "white"
    if n == 3 and val >= 3: return COLOR_ELITE, "white"
    if n == 2 and val >= 2: return COLOR_ELITE, "white"
    if n == 1 and val >= 1: return COLOR_ELITE, "white"
    
    # Bom
    if n == 5 and val >= 3: return COLOR_BOM, "#081C15"
    if n == 4 and val >= 3: return COLOR_BOM, "#081C15"
    if n == 3 and val >= 2: return COLOR_BOM, "#081C15"
    if n == 2 and val >= 1: return COLOR_BOM, "#081C15"
    
    # Médio
    if n == 5 and val >= 2: return COLOR_MEDIA, "#081C15"
    if n == 4 and val >= 2: return COLOR_MEDIA, "#081C15"
    if n == 3 and val >= 1: return COLOR_MEDIA, "#081C15"
    
    # Fallback para janelas maiores/outras
    if n > 5:
        ratio = val / n
        if ratio >= 0.8: return COLOR_ELITE, "white"
        if ratio >= 0.6: return COLOR_BOM, "#081C15"
        if ratio >= 0.4: return COLOR_MEDIA, "#081C15"
        
    return COLOR_ROW_ODD, "black"


def get_sg_color_zag(val, n_jogos):
    """SG exclusivo para zagueiros.

    Regras (proporcional à janela):
      - verde escuro se val == n_jogos  (SG em todos os jogos)
      - verde claro  se val / n_jogos >= 2/3
      - branco nos demais casos
    Sem verde médio.

    Exemplos:
      n=3: 0/1 → branco | 2 → claro | 3 → escuro
      n=4: 0/1/2 → branco | 3 → claro | 4 → escuro
      n=5: 0/1/2/3 → branco | 4 → claro | 5 → escuro
    """
    TXT = "black"
    if n_jogos <= 0:
        return COLOR_DEFAULT, TXT
    if val >= n_jogos:
        return COLOR_ELITE, "white"
    if val / n_jogos >= (2.0 / 3.0):
        return COLOR_MEDIA, TXT
    return COLOR_DEFAULT, TXT


def get_sg_color_laterais(val, n_jogos):
    """SG exclusivo para laterais — mais restritivo que goleiros.

    Janela 3: 0-1 → branco  |  2 → verde claro  |  3 → verde escuro
    Escala proporcional para outras janelas (limiar claro = 2/3 × n_jogos).
    Não usa verde médio nesta posição.
    """
    TXT = "black"
    lim_elite = float(n_jogos)          # 3 para janela=3
    lim_claro = (2.0 / 3.0) * n_jogos  # 2 para janela=3

    if val >= lim_elite:
        return COLOR_ELITE, "white"
    if val >= lim_claro:
        return COLOR_MEDIA, TXT
    return COLOR_DEFAULT, TXT


def get_color_for_value(col_name, value, n_jogos, position_type="MEIAS"):
    if value <= 0: return COLOR_ROW_ODD, "black" # Sem destaque
    
    is_avg = False
    
    # 1. Definir Limites Base (POR JOGO)
    # AF: Elite 8/jogo, Bom 6/jogo, Media 4/jogo (?) - (User provided high numbers, implementing literally)
    # CHUTES: Elite 7/jogo, Bom 4/jogo, Media 3/jogo
    # PG: Elite 3/jogo, Bom 2/jogo, Media 1/jogo
    # BÁSICA: Elite 3.5, Bom 2.5, Media 1.5 (Valores fixos média)
    
    if "AF" in col_name:
        if position_type == "ATACANTES":
            # Passe fin. é pré-scout para atacantes — limiar mais exigente
            lim_elite, lim_bom, lim_media = 5.0, 4.0, 3.0
        else:
            lim_elite, lim_bom, lim_media = 5.0, 4.0, 3.0
    elif "CHUTES" in col_name:
        if position_type == "ATACANTES":
            # Atacantes exigem volume alto de finalização — limiar elevado
            lim_elite, lim_bom, lim_media = 7.0, 6.0, 5.0
        else:
            lim_elite, lim_bom, lim_media = 5.0, 4.0, 3.0
    elif "PG" in col_name:
        lim_elite, lim_bom, lim_media = 3.0, 2.0, 1.0
    elif "BASICA" in col_name:
        # Meias e Atacantes: piso claro em 2.0
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
    # Para médias (BASICA), arredonda para 1 casa decimal para evitar
    # falsos negativos por imprecisão de ponto flutuante
    # (ex: 2.6999...97 exibido como 2,7 mas falhando >= 2.7)
    cmp = float(f"{float(value):.1f}") if is_avg else value

    if cmp >= t_elite:
        return COLOR_ELITE, "white"
    elif cmp >= t_bom:
        return COLOR_BOM, "#081C15"
    elif cmp >= t_media:
        return COLOR_MEDIA, "#081C15"

    return COLOR_ROW_ODD, "black"

def get_color_zag(col_name, value, n_jogos):
    """Coloração exclusiva para a tabela de ZAGUEIROS.

    SG      → get_sg_color_zag() (exclusivo — não usa get_sg_color global)
    DE      → escala com n_jogos: 2×n claro | 3×n médio | 4×n escuro (inalterada)
    CHUTES  → proporcional (FINALIZ.): ceil(2/3×n) claro | ceil(4/3×n) médio | ceil(5/3×n) escuro
    PTS     → absoluto (MÉD. PTS): <3.0 branco | 3.0 claro | 4.5 médio | 6.0 escuro
    BASICA  → absoluto (MÉD. BÁSICA): <1.8 branco | 1.8 claro | 2.2 médio | 2.6 escuro
    """
    TXT = "black"

    if value <= 0:
        return COLOR_ROW_ODD, TXT

    # 1. SG — regra específica para zagueiros (não usa get_sg_color global)
    if "SG" in col_name:
        return get_sg_color_zag(value, n_jogos)

    # 2. DE — Desarmes, escala com n_jogos (mantida intacta)
    if "DE" in col_name:
        f = float(n_jogos)
        if   value >= 4.0 * f: return COLOR_ELITE, "white"
        elif value >= 3.0 * f: return COLOR_BOM,   TXT
        elif value >= 2.0 * f: return COLOR_MEDIA,  TXT
        return COLOR_ROW_ODD, TXT

    # 3. CHUTES / FINALIZ. — limiar proporcional à janela
    if "CHUTES" in col_name:
        lim_claro = math.ceil((2.0 / 3.0) * n_jogos)
        lim_bom   = math.ceil((4.0 / 3.0) * n_jogos)
        lim_elite = math.ceil((5.0 / 3.0) * n_jogos)
        if   value >= lim_elite: return COLOR_ELITE, "white"
        elif value >= lim_bom:   return COLOR_BOM,   TXT
        elif value >= lim_claro: return COLOR_MEDIA,  TXT
        return COLOR_ROW_ODD, TXT

    # 4. PTS / MÉD. PTS — média por jogo (valor absoluto)
    if "PTS" in col_name:
        if   value >= 6.0: return COLOR_ELITE, "white"
        elif value >= 4.5: return COLOR_BOM,   TXT
        elif value >= 3.0: return COLOR_MEDIA,  TXT
        return COLOR_ROW_ODD, TXT

    # 5. BASICA / MÉD. BÁSICA — média por jogo (valor absoluto)
    if "BASICA" in col_name:
        if   value >= 2.6: return COLOR_ELITE, "white"
        elif value >= 2.2: return COLOR_BOM,   TXT
        elif value >= 1.8: return COLOR_MEDIA,  TXT
        return COLOR_ROW_ODD, TXT

    return COLOR_ROW_ODD, TXT

def get_color_gol(col_name, value, n_jogos):
    TXT_BLACK = "black"
    
    try:
        val = float(value)
    except:
        return COLOR_DEFAULT, TXT_BLACK

    # 1. CHUTES A GOL (AG) ou CHUTES GERAIS
    if "CHUT. AG" in col_name or "_CHUTES_AG" in col_name:
        if val >= 6.0 * n_jogos: return COLOR_ELITE, TXT_BLACK
        elif val >= 5.0 * n_jogos: return COLOR_BOM, TXT_BLACK
        elif val >= 4.0 * n_jogos: return COLOR_CLARO, TXT_BLACK
        return COLOR_DEFAULT, TXT_BLACK

    # 2. CHUTES PM (Para Marcar)
    # Regra: Elite 5, Bom 4, Claro 3
    elif "CHUT. PM" in col_name or "_PM" in col_name:
        if val >= 5.0: return COLOR_ELITE, TXT_BLACK
        elif val >= 4.0: return COLOR_BOM, TXT_BLACK
        elif val >= 3.0: return COLOR_CLARO, TXT_BLACK
        return COLOR_DEFAULT, TXT_BLACK

    # 3. DEFESAS (DE)
    elif "DE" in col_name and "%" not in col_name and "PCT" not in col_name:
        if val >= 5.0 * n_jogos: return COLOR_ELITE, TXT_BLACK
        elif val >= 4.0 * n_jogos: return COLOR_BOM, TXT_BLACK
        elif val >= 3.0 * n_jogos: return COLOR_CLARO, TXT_BLACK
        return COLOR_DEFAULT, TXT_BLACK

    # 4. % DE (% Defesas)
    elif "% DE" in col_name or "PCT_DE" in col_name:
        if val >= 80.0: return COLOR_ELITE, TXT_BLACK
        elif val >= 67.0: return COLOR_BOM, TXT_BLACK
        elif val >= 60.0: return COLOR_CLARO, TXT_BLACK
        return COLOR_DEFAULT, TXT_BLACK

    # 5. GOLS (Inverso - Menor é melhor)
    elif "GOLS" in col_name:
        if n_jogos >= 5:
            if val <= 1: return COLOR_ELITE, TXT_BLACK
            elif val <= 2: return COLOR_BOM, TXT_BLACK
            elif val <= 3: return COLOR_CLARO, TXT_BLACK
        elif n_jogos >= 3:
            if val <= 0: return COLOR_ELITE, TXT_BLACK
            elif val <= 1: return COLOR_BOM, TXT_BLACK
            elif val <= 2: return COLOR_CLARO, TXT_BLACK
        elif n_jogos == 2:
            if val <= 0: return COLOR_ELITE, TXT_BLACK
            elif val <= 1: return COLOR_BOM, TXT_BLACK
        elif n_jogos == 1:
            if val <= 0: return COLOR_ELITE, TXT_BLACK
        
        return COLOR_DEFAULT, TXT_BLACK

    # 6. SG (Clean Sheets)
    elif "SG" in col_name:
        return get_sg_color(val, n_jogos)

    return COLOR_DEFAULT, TXT_BLACK


def get_color_gol_pct_de(value, pressao_index):
    """
    Regra de cor exclusiva para % DEFESAS na tabela de goleiros.
    A cor só aparece quando há TANTO bom percentual QUANTO pressão suficiente.
      Sem cor  : %DEF < 70  OU  pressao < 12
      Claro    : %DEF >= 70 E pressao >= 12 E pressao < 15
      Médio    : %DEF >= 70 E pressao >= 15 E pressao < 18
      Escuro   : %DEF >= 70 E pressao >= 18
    """
    TXT_BLACK = "black"
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    try:
        pressao = float(pressao_index)
    except (TypeError, ValueError):
        pressao = 0.0

    if pct < 70.0 or pressao < 12.0:
        return COLOR_DEFAULT, TXT_BLACK

    if pressao >= 18.0:
        return COLOR_ELITE, TXT_BLACK
    elif pressao >= 15.0:
        return COLOR_BOM, TXT_BLACK
    else:  # >= 12
        return COLOR_CLARO, TXT_BLACK


def get_color_gol_gols(value):
    """
    Regra de cor exclusiva para GOLS na tabela de goleiros.
      0      → verde claro (favorável ao goleiro)
      1 a 4  → branco (neutro)
      >= 5   → vermelho claro (risco relevante)
    """
    TXT_BLACK = "black"
    try:
        val = float(value)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    if val == 0:
        return "#C8E6C9", TXT_BLACK   # verde claro discreto
    elif val >= 5:
        return "#FECACA", TXT_BLACK   # vermelho claro / salmão
    else:
        return COLOR_DEFAULT, TXT_BLACK  # branco (1–4)


def get_color_gol_chutes_ag(value, risco_index, chute_pm_cruzado):
    """
    Cor para CHUTE A GOL na tabela de goleiros.
    Prioridade: vermelho primeiro (contexto de ameaça sobrepõe verde).
      Vermelho forte : val>=15 E (risco>=5 OU pm<3)
      Vermelho claro : val>=12 E (risco>=5 OU pm<3)
      Verde forte    : val>=15 E risco<5 E pm>=5
      Verde claro    : val>=12 E risco<5 E pm>=4
      Branco         : demais casos
    """
    TXT_BLACK = "black"
    try:
        val   = float(value)
        risco = float(risco_index)
        pm    = float(chute_pm_cruzado)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    ameaca = risco >= 5 or pm < 3

    if val >= 15 and ameaca:
        return "#FCA5A5", TXT_BLACK   # vermelho forte
    if val >= 12 and ameaca:
        return "#FECACA", TXT_BLACK   # vermelho claro
    if val >= 15 and not ameaca and pm >= 5:
        return "#81C784", TXT_BLACK   # verde forte
    if val >= 12 and not ameaca and pm >= 4:
        return "#C8E6C9", TXT_BLACK   # verde claro
    return COLOR_DEFAULT, TXT_BLACK


def get_color_gol_chutes_pm(value, pressao_index, risco_index):
    """
    Cor para CHUTE P/ MARCAR na tabela de goleiros.
    Prioridade: vermelho primeiro.
      Vermelho forte : val<3 E (pressao>=15 OU risco>=5)
      Vermelho claro : val<3 E pressao>=12
      Verde forte    : val>=5 E pressao>=15 E risco<5
      Verde claro    : val>=4 E pressao>=12 E risco<5
      Branco         : demais casos
    """
    TXT_BLACK = "black"
    try:
        val     = float(value)
        pressao = float(pressao_index)
        risco   = float(risco_index)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    if val < 3 and (pressao >= 15 or risco >= 5):
        return "#FCA5A5", TXT_BLACK   # vermelho forte
    if val < 3 and pressao >= 12:
        return "#FECACA", TXT_BLACK   # vermelho claro
    if val >= 5 and pressao >= 15 and risco < 5:
        return "#81C784", TXT_BLACK   # verde forte
    if val >= 4 and pressao >= 12 and risco < 5:
        return "#C8E6C9", TXT_BLACK   # verde claro
    return COLOR_DEFAULT, TXT_BLACK


def get_color_gol_defesas(value, risco_index):
    """
    Cor para DEFESAS na tabela de goleiros. Apenas verde ou branco — nunca vermelho.

    Regras (limiar elevado para ser mais seletivo):
      val < 8                          → branco
      val >= 8 e < 11 e risco < 5     → verde claro  (#C8E6C9)
      val >= 11 e risco < 5           → verde forte   (#81C784)
      val >= 11 e risco >= 5          → verde claro   (#C8E6C9)  (risco alto limita)
      val >= 8 e < 11 e risco >= 5    → branco
    """
    TXT_BLACK = "black"
    try:
        val   = float(value)
        risco = float(risco_index)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    if val >= 11 and risco < 5:
        return "#81C784", TXT_BLACK   # verde forte
    if val >= 11 and risco >= 5:
        return "#C8E6C9", TXT_BLACK   # verde claro (risco alto limita destaque)
    if val >= 8 and risco < 5:
        return "#C8E6C9", TXT_BLACK   # verde claro
    return COLOR_DEFAULT, TXT_BLACK   # branco (val<8, ou val 8-10 com risco>=5)


def get_color_gol_sg(value, risco_index):
    """
    Cor para SG na tabela de goleiros. Apenas verde ou branco.
      Verde forte : val>=2 E risco<5
      Verde claro : val>=1 E risco<5
      Verde claro : val>=2 E risco>=5  (risco alto limita a verde claro)
      Branco      : demais casos (incluindo val=0)
    """
    TXT_BLACK = "black"
    try:
        val   = float(value)
        risco = float(risco_index)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT_BLACK

    if val >= 2 and risco < 5:
        return "#81C784", TXT_BLACK   # verde forte
    if val >= 1 and risco < 5:
        return "#C8E6C9", TXT_BLACK   # verde claro
    if val >= 2 and risco >= 5:
        return "#C8E6C9", TXT_BLACK   # verde claro (risco alto limita destaque)
    return COLOR_DEFAULT, TXT_BLACK


def get_color_perfil_gol(perfil):
    """Cor de fundo para as células de PERFIL do goleiro (sem verde)."""
    return PERFIL_BG_COLORS.get(perfil, "#F3F4F6")


def get_color_lat(col_name, value, n_jogos):
    """Coloração exclusiva para a tabela de LATERAIS.

    Regras calibradas para janela de 3 jogos (escalam proporcionalmente):

    DESARMES (_DE):
        ≥ 10/3 × n_jogos → verde escuro   (≥10 em janela=3)
        ≥  8/3 × n_jogos → verde médio    (≥ 8 em janela=3)
        ≥  2.0 × n_jogos → verde claro    (≥ 6 em janela=3)
        abaixo           → branco

    G + A (_PG):
        ≥ 3 → verde escuro
        ≥ 2 → verde médio
        ≥ 1 → verde claro
        0   → branco

    MÉD. BÁSICA (_BAS):
        ≥ 4.0 → verde escuro
        ≥ 3.5 → verde médio
        ≥ 2.5 → verde claro
        < 2.5 → branco

    SG (_SG):  via get_sg_color_laterais()
        0-1   → branco
        ≥ 2   → verde claro  (≥ 2/3 × n_jogos)
        ≥ n   → verde escuro (todos os jogos)
    """
    TXT = "black"

    try:
        val = float(value)
    except (TypeError, ValueError):
        return COLOR_DEFAULT, TXT

    # DE — Desarmes
    if "_DE" in col_name and "PCT" not in col_name:
        if   val >= (10.0 / 3.0) * n_jogos: return COLOR_ELITE, TXT
        elif val >= ( 8.0 / 3.0) * n_jogos: return COLOR_BOM,   TXT
        elif val >= ( 6.0 / 3.0) * n_jogos: return COLOR_MEDIA, TXT

    # PG — Gols + Assistências
    elif "_PG" in col_name:
        if   val >= 3: return COLOR_ELITE, TXT
        elif val >= 2: return COLOR_BOM,   TXT
        elif val >= 1: return COLOR_MEDIA, TXT

    # BAS — Média Básica
    elif "_BAS" in col_name:
        if   val >= 4.0: return COLOR_ELITE, TXT
        elif val >= 3.5: return COLOR_BOM,   TXT
        elif val >= 2.5: return COLOR_MEDIA, TXT

    # SG — regra específica para laterais (não usa get_sg_color global)
    elif "_SG" in col_name:
        return get_sg_color_laterais(val, n_jogos)

    return COLOR_DEFAULT, TXT

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
    fig, ax = plt.subplots(figsize=(24, len(df) * 1.1 + 7 + extra_h), dpi=200)
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
        ("PASSE FIN.", 0, 2),
        ("FINALIZ.", 2, 4),
        ("G + A", 4, 6),
        ("MÉD. BÁSICA", 6, 8),
        ("MANDO", 8, 9),
        ("PASSE FIN.", 9, 11),
        ("FINALIZ.", 11, 13),
        ("G + A", 13, 15),
        ("MÉD. BÁSICA", 15, 17),
    ]
    
    for label, start_idx, end_idx in groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        edge_color = "white" if start_idx % 2 == 0 and start_idx > 0 else "none"
        edge_width = 2 if edge_color == "white" else 0
        
        if label != "MANDO":
            draw_gradient_rect(ax, x_start, super_header_y, width, super_header_h,
                               GRAD_SCOUTS[0], GRAD_SCOUTS[1], zorder=100)
        else:
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor=COLOR_TCC_GREEN, edgecolor="none", linewidth=0,
                transform=ax.transAxes, zorder=100
            ))
        if edge_color != "none":
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor="none", edgecolor=edge_color, linewidth=edge_width,
                transform=ax.transAxes, zorder=103
            ))

        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=13, transform=ax.transAxes, zorder=104)

    # === SUB HEADERS - COLADO ===
    sub_header_y = super_header_y - super_header_h - 0.02  # deslocado para dar altura ao texto duplo
    sub_header_h = 0.062
    COLOR_CINZA = "#E5E7EB"

    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA X FORA"  # Texto aqui, UMA vez só
        else:
            prefix = col.split("_")[0]
            bg_color = COLOR_TCC_PINK if prefix in ["COC", "COF"] else COLOR_CINZA
            label = PREFIX_LABELS.get(prefix, prefix)

        # Desenhar retângulo SEM BORDAS
        rect = patches.Rectangle(
            (curr_x, sub_header_y), col_widths[i], sub_header_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)

        ax.text(curr_x + col_widths[i]/2, sub_header_y + sub_header_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=8 if col == "MANDO" else 7.0, family="DejaVu Sans",
                multialignment="center", linespacing=1.6,
                transform=ax.transAxes, zorder=52)
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
                # Usar nova função de cor (passa position_type para BASICA meias vs. atacantes)
                cell_color, text_color = get_color_for_value(col, val, window_n, position_type)
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
    fig, ax = plt.subplots(figsize=(24, len(df) * 1.1 + 7 + extra_h), dpi=200) # Largura um pouco maior pra 5 colunas
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
        ("SG", 0, 2),
        ("DESARMES", 2, 4),
        ("FINALIZ.", 4, 6),
        ("MÉD. PTS", 6, 8),
        ("MÉD. BÁSICA", 8, 10),
        ("MANDO", 10, 11),
        ("SG", 11, 13),
        ("DESARMES", 13, 15),
        ("FINALIZ.", 15, 17),
        ("MÉD. PTS", 17, 19),
        ("MÉD. BÁSICA", 19, 21),
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

        if label != "MANDO":
            draw_gradient_rect(ax, x_start, super_header_y, width, super_header_h,
                               GRAD_SCOUTS[0], GRAD_SCOUTS[1], zorder=100)
        else:
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor=COLOR_TCC_GREEN, edgecolor="none", linewidth=0,
                transform=ax.transAxes, zorder=100
            ))
        if edge_color != "none":
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor="none", edgecolor=edge_color, linewidth=edge_width,
                transform=ax.transAxes, zorder=103
            ))
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=11, transform=ax.transAxes, zorder=104)

    # === SUB HEADERS ===
    sub_header_y = super_header_y - super_header_h - 0.02
    sub_header_h = 0.062
    COLOR_CINZA = "#E5E7EB"

    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA X FORA"
        else:
            prefix = col.split("_")[0]
            bg_color = COLOR_TCC_PINK if prefix in ["COC", "COF"] else COLOR_CINZA
            label = PREFIX_LABELS.get(prefix, prefix)

        rect = patches.Rectangle(
            (curr_x, sub_header_y), col_widths[i], sub_header_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)

        ax.text(curr_x + col_widths[i]/2, sub_header_y + sub_header_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=8 if col == "MANDO" else 7.0, family="DejaVu Sans",
                multialignment="center", linespacing=1.6,
                transform=ax.transAxes, zorder=52)
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

    # === ROWS ===

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
    Renderiza tabela de GOLEIROS (Pressão / Risco / Potencial)
    """
    df = df_original.reset_index(drop=True)
    
    extra_h = 1.0 if exibir_legenda else 0
    # Tabela mais larga (12 cols por lado vs 10 antes) -> Aumentar width de 24 para 28
    fig, ax = plt.subplots(figsize=(28, len(df) * 1.1 + 7 + extra_h), dpi=200)
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
            
    # === ESTRUTURA DA TABELA GOLEIROS (Pressão / Risco / Potencial + PERFIL) ===
    # Left : Pressão [COF/CDC] | Risco [COF/CDC] | Potencial [COC/CDF]
    # Center: PERFIL_MANDANTE | MANDO | PERFIL_VISITANTE
    # Right : Potencial [COF/CDC] | Risco [COF/CDC] | Pressão [COC/CDF]
    cols_left = [
        "COF_CHUTES_AG", "CDC_CHUTES_AG",    # idx  0-1  PRESSÃO
        "COF_CHUTES_PM", "CDC_CHUTES_PM",    # idx  2-3
        "COF_GOLS", "CDC_GOLS",              # idx  4-5  RISCO
        "COC_DE", "CDF_DE",                  # idx  6-7  POTENCIAL
        "COC_PCT_DE", "CDF_PCT_DE",          # idx  8-9
        "COC_SG", "CDF_SG",                  # idx 10-11
    ]
    cols_center = ["PERFIL_MANDANTE", "MANDO", "PERFIL_VISITANTE"]  # idx 12, 13, 14
    cols_right = [
        "COC_CHUTES_AG", "CDF_CHUTES_AG",    # idx 15-16 PRESSÃO
        "COC_CHUTES_PM", "CDF_CHUTES_PM",    # idx 17-18
        "COC_GOLS", "CDF_GOLS",              # idx 19-20 RISCO
        "COF_DE", "CDC_DE",                  # idx 21-22 POTENCIAL
        "COF_PCT_DE", "CDC_PCT_DE",          # idx 23-24
        "COF_SG", "CDC_SG",                  # idx 25-26
    ]

    all_cols = cols_left + cols_center + cols_right

    # Larguras: 24 colunas de dados (0.032 cada) + 2 PERFIL (0.055 cada) + MANDO (0.10)
    # Total = 24*0.032 + 2*0.055 + 0.10 = 0.768 + 0.110 + 0.10 = 0.978 → cabe.
    col_w    = 0.032   # dados
    perfil_w = 0.055   # PERFIL: largo o suficiente para "SG+ DEFESAS" / "ALTO RISCO"
    col_widths = [col_w] * 12 + [perfil_w] + [0.10] + [perfil_w] + [col_w] * 12
    
    # Calcular start_x para centralizar
    total_w = sum(col_widths)
    start_x = (1 - total_w) / 2
    
    # === SUPER HEADERS (AMEAÇAS / OPORTUNIDADES) ===
    # AJUSTE: Descer tabela para não sobrepor subtitulo
    super_header_y = 0.79 # Era 0.82
    super_header_h = 0.05 # Era 0.04 (Aumentado levemente)
    
    # Grupos Lógicos
    # Indices:
    # 0-3  (2 métricas x 2) = PRESSÃO   (CHUTE A GOL, CHUTE P/ MARCAR)
    # 4-5  (1 métrica  x 2) = RISCO     (GOLS)
    # 6-11 (3 métricas x 2) = POTENCIAL (DEFESAS, SG, % DEFESAS)
    # 12 = MANDO
    # 13-16 = PRESSÃO (Right)
    # 17-18 = RISCO (Right)
    # 19-24 = POTENCIAL (Right)
    
    # Cores Headers Topo (mantidas como chaves do mapa de gradiente)
    COLOR_PRESSAO   = "#90CAF9"
    COLOR_RISCO     = "#EF9A9A"
    COLOR_POTENCIAL = "#FFCC80"
    _GRAD_GOL = {
        COLOR_PRESSAO:   GRAD_PRESSAO,
        COLOR_RISCO:     GRAD_RISCO,
        COLOR_POTENCIAL: GRAD_POTENCIAL,
    }

    top_groups = [
        # Lado esquerdo (idx 0-11 = dados, idx 12 = PERFIL_MAN → sem bloco topo)
        ("PRESSÃO",    0,  4, COLOR_PRESSAO),    # CHUTE A GOL + CHUTE P/ MARCAR
        ("RISCO",      4,  6, COLOR_RISCO),       # GOLS
        ("POTENCIAL",  6, 12, COLOR_POTENCIAL),   # DEFESAS + % DEFESAS + SG
        # idx 12 PERFIL_MAN, idx 13 MANDO, idx 14 PERFIL_VIS → sem bloco topo (zona central)
        # Lado direito (idx 15-26 = dados, +2 em relação ao layout anterior)
        ("PRESSÃO",   15, 19, COLOR_PRESSAO),
        ("RISCO",     19, 21, COLOR_RISCO),
        ("POTENCIAL", 21, 27, COLOR_POTENCIAL),
    ]
    
    # Desenhar Top Level Headers
    top_header_y = super_header_y + 0.05 # Acima do Subheader verde
    top_header_h = 0.045
    
    for label, start_idx, end_idx, color in top_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        grad = _GRAD_GOL.get(color, (color, color))
        draw_gradient_rect(ax, x_start, top_header_y, width, top_header_h,
                           grad[0], grad[1], zorder=100)
        ax.add_patch(patches.Rectangle(
            (x_start, top_header_y), width, top_header_h,
            facecolor="none", edgecolor="white", linewidth=1,
            transform=ax.transAxes, zorder=102
        ))
        ax.text(x_start + width/2, top_header_y + top_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=13, transform=ax.transAxes, zorder=103)

    # === SUB HEADERS (Verdes: CHUT.AG, CHUT.PM...) ===
    # Agora sim os headers verdes padrão
    
    sub_groups = [
        # Lado esquerdo
        ("CHUTE A GOL",     0,  2),
        ("CHUTE P/ MARCAR", 2,  4),
        ("GOLS",            4,  6),
        ("DEFESAS",         6,  8),
        ("% DEFESAS",       8, 10),
        ("SG",             10, 12),
        # Centro
        ("PERFIL",         12, 13),   # cabeçalho PERFIL mandante
        ("MANDO",          13, 14),
        ("PERFIL",         14, 15),   # cabeçalho PERFIL visitante
        # Lado direito (shift +2)
        ("CHUTE A GOL",    15, 17),
        ("CHUTE P/ MARCAR",17, 19),
        ("GOLS",           19, 21),
        ("DEFESAS",        21, 23),
        ("% DEFESAS",      23, 25),
        ("SG",             25, 27),
    ]
    
    for label, start_idx, end_idx in sub_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])

        # Cabeçalho PERFIL em grafite; demais em verde padrão
        if label == "PERFIL":
            subh_bg = COLOR_PERFIL_HEADER
        else:
            subh_bg = COLOR_TCC_GREEN

        if label == "MANDO":
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor=COLOR_TCC_GREEN, edgecolor="none", linewidth=0,
                transform=ax.transAxes, zorder=100
            ))
        elif label == "PERFIL":
            draw_gradient_rect(ax, x_start, super_header_y, width, super_header_h,
                               GRAD_PERFIS[0], GRAD_PERFIS[1], zorder=100)
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor="none", edgecolor="white", linewidth=1,
                transform=ax.transAxes, zorder=102
            ))
        else:
            draw_gradient_rect(ax, x_start, super_header_y, width, super_header_h,
                               GRAD_SCOUTS[0], GRAD_SCOUTS[1], zorder=100)
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor="none", edgecolor="white", linewidth=1,
                transform=ax.transAxes, zorder=102
            ))
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=9, transform=ax.transAxes, zorder=103)

    # === DATA LABELS (COC/CDF/COF/CDC) ===
    data_labels_h = 0.062
    data_labels_y = super_header_y - data_labels_h
    COLOR_CINZA = "#E5E7EB"

    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            bg_color = "white"
            label = "CASA • FORA"
            fsize = 9.5
        elif col in ("PERFIL_MANDANTE", "PERFIL_VISITANTE"):
            # Coluna PERFIL: texto interpretativo no lugar do COC/CDF
            bg_color = "#F3F4F6"  # cinza muito claro
            label = "INDICADO\nPARA"
            fsize = 10.0
        else:
            prefix = col.split("_")[0] # COC, CDF, COF, CDC
            if prefix in ["COC", "COF"]:
                bg_color = COLOR_TCC_PINK
            else:
                bg_color = COLOR_CINZA
            label = PREFIX_LABELS.get(prefix, prefix)
            fsize = 7.0

        rect = patches.Rectangle(
            (curr_x, data_labels_y), col_widths[i], data_labels_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)

        ax.text(curr_x + col_widths[i]/2, data_labels_y + data_labels_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=fsize, family="DejaVu Sans",
                multialignment="center", linespacing=1.6,
                transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]

    # Bordas Linha Labels
    ax.plot([start_x, start_x + sum(col_widths)], [data_labels_y, data_labels_y],
           color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
           
    # Verticais Labels
    for i in range(len(col_widths) + 1): # +1 Para fechar a ultima borda
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, data_labels_y + data_labels_h],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === ROWS ===
        
        
    # === ROWS ===
    row_h = 0.065
    curr_y = data_labels_y
    for idx in range(len(df)):
        curr_y -= row_h
        curr_x = start_x
        row_color = "white" # REMOVIDO ZEBRADO: Sempre Branco

        for i, col in enumerate(all_cols):
            # MANDO e PERFIL não são numéricos — lidos dentro de cada bloco
            _skip_val = col in ("MANDO", "PERFIL_MANDANTE", "PERFIL_VISITANTE")
            val = None if _skip_val else df.iloc[idx][col]

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

            elif col in ("PERFIL_MANDANTE", "PERFIL_VISITANTE"):
                # === PERFIL CELL ===
                perfil_val = str(df.iloc[idx].get(col, "-")) if col in df.columns else "-"
                if perfil_val in ("nan", "None", ""):
                    perfil_val = "-"
                bg_c = get_color_perfil_gol(perfil_val)
                display_txt = PERFIL_DISPLAY.get(perfil_val, perfil_val)

                # Fundo
                rect = patches.Rectangle((curr_x, curr_y), col_widths[i], row_h,
                    facecolor=bg_c, edgecolor="none", linewidth=0,
                    transform=ax.transAxes, zorder=10)
                ax.add_patch(rect)

                # Bordas laterais mais marcadas (selo interpretativo)
                ax.plot([curr_x, curr_x], [curr_y, curr_y + row_h],
                        color=COLOR_PERFIL_HEADER, linewidth=1.5,
                        transform=ax.transAxes, zorder=20)
                ax.plot([curr_x + col_widths[i], curr_x + col_widths[i]],
                        [curr_y, curr_y + row_h],
                        color=COLOR_PERFIL_HEADER, linewidth=1.5,
                        transform=ax.transAxes, zorder=20)

                # Texto (2 linhas para SG+DEFESAS e ALTO RISCO, 1 linha para o resto)
                ax.text(curr_x + col_widths[i]/2, curr_y + row_h/2, display_txt,
                       ha="center", va="center", color="#1E293B", weight="bold",
                       fontsize=11, family="DejaVu Sans",
                       multialignment="center", linespacing=1.4,
                       transform=ax.transAxes, zorder=15)

            else:
                # DADOS CELL
                if "PM" in col: fmt = "{:.1f}"
                elif "PCT" in col: fmt = "{:.0f}%"
                elif "GOLS" in col or "DE" in col or "SG" in col or "CHUTES" in col: 
                    fmt = "{:.0f}"
                else: fmt = "{:.1f}"
                
                txt = fmt.format(val)

                # Cor — PCT_DE usa regra contextual (pressão + percentual)
                if "PCT_DE" in col:
                    row_data = df.iloc[idx]
                    def _safe(k):
                        try: return float(row_data.get(k, 0) or 0)
                        except (TypeError, ValueError): return 0.0
                    if col in ("COC_PCT_DE", "CDF_PCT_DE"):
                        # Goleiro MANDANTE: pressão vem dos chutes do visitante
                        pressao = (_safe("COF_CHUTES_AG") + _safe("CDC_CHUTES_AG")) / 2
                    else:
                        # Goleiro VISITANTE: pressão vem dos chutes do mandante
                        pressao = (_safe("COC_CHUTES_AG") + _safe("CDF_CHUTES_AG")) / 2
                    bg_c, txt_c = get_color_gol_pct_de(val, pressao)
                elif "GOLS" in col:
                    # GOLS: 0=verde, 1-4=branco, >=5=vermelho
                    bg_c, txt_c = get_color_gol_gols(val)
                elif "CHUTES_AG" in col:
                    # CHUTE A GOL: contextual (risco + pm cruzado)
                    row_data = df.iloc[idx]
                    def _safe_ag(k):
                        try: return float(row_data.get(k, 0) or 0)
                        except (TypeError, ValueError): return 0.0
                    if col in ("COF_CHUTES_AG", "CDC_CHUTES_AG"):
                        risco_ctx = (_safe_ag("COF_GOLS")     + _safe_ag("CDC_GOLS"))     / 2
                        pm_ctx    = (_safe_ag("COF_CHUTES_PM") + _safe_ag("CDC_CHUTES_PM")) / 2
                    else:
                        risco_ctx = (_safe_ag("COC_GOLS")     + _safe_ag("CDF_GOLS"))     / 2
                        pm_ctx    = (_safe_ag("COC_CHUTES_PM") + _safe_ag("CDF_CHUTES_PM")) / 2
                    bg_c, txt_c = get_color_gol_chutes_ag(val, risco_ctx, pm_ctx)
                elif "CHUTES_PM" in col:
                    # CHUTE P/ MARCAR: contextual (pressao + risco)
                    row_data = df.iloc[idx]
                    def _safe_pm(k):
                        try: return float(row_data.get(k, 0) or 0)
                        except (TypeError, ValueError): return 0.0
                    if col in ("COF_CHUTES_PM", "CDC_CHUTES_PM"):
                        pressao_ctx = (_safe_pm("COF_CHUTES_AG") + _safe_pm("CDC_CHUTES_AG")) / 2
                        risco_ctx   = (_safe_pm("COF_GOLS")      + _safe_pm("CDC_GOLS"))      / 2
                    else:
                        pressao_ctx = (_safe_pm("COC_CHUTES_AG") + _safe_pm("CDF_CHUTES_AG")) / 2
                        risco_ctx   = (_safe_pm("COC_GOLS")      + _safe_pm("CDF_GOLS"))      / 2
                    bg_c, txt_c = get_color_gol_chutes_pm(val, pressao_ctx, risco_ctx)
                elif "PCT" not in col and "_DE" in col:
                    # DEFESAS: verde ou branco contextual (risco do lado)
                    row_data = df.iloc[idx]
                    def _safe_de(k):
                        try: return float(row_data.get(k, 0) or 0)
                        except (TypeError, ValueError): return 0.0
                    if col in ("COC_DE", "CDF_DE"):   # mandante
                        risco_ctx = (_safe_de("COF_GOLS") + _safe_de("CDC_GOLS")) / 2
                    else:                              # visitante
                        risco_ctx = (_safe_de("COC_GOLS") + _safe_de("CDF_GOLS")) / 2
                    bg_c, txt_c = get_color_gol_defesas(val, risco_ctx)
                elif "_SG" in col:
                    # SG: verde ou branco contextual (risco do lado)
                    row_data = df.iloc[idx]
                    def _safe_sg(k):
                        try: return float(row_data.get(k, 0) or 0)
                        except (TypeError, ValueError): return 0.0
                    if col in ("COC_SG", "CDF_SG"):   # mandante
                        risco_ctx = (_safe_sg("COF_GOLS") + _safe_sg("CDC_GOLS")) / 2
                    else:                              # visitante
                        risco_ctx = (_safe_sg("COC_GOLS") + _safe_sg("CDF_GOLS")) / 2
                    bg_c, txt_c = get_color_gol_sg(val, risco_ctx)
                else:
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
    
    # Separadores verticais: limites de grupo (inclui PERFIL em 12, 13, 14, 15)
    gol_vert_indices = [2, 4, 6, 8, 10, 12, 13, 14, 15, 17, 19, 21, 23, 25]

    for i in gol_vert_indices:
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, curr_y],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=202)

    # Bordas grafite mais fortes nas laterais das colunas PERFIL (selo interpretativo)
    for perfil_start_idx, perfil_end_idx in [(12, 13), (14, 15)]:
        x_left  = start_x + sum(col_widths[:perfil_start_idx])
        x_right = start_x + sum(col_widths[:perfil_end_idx])
        ax.plot([x_left,  x_left],  [super_header_y, curr_y],
                color=COLOR_PERFIL_HEADER, linewidth=2.0,
                transform=ax.transAxes, zorder=203)
        ax.plot([x_right, x_right], [super_header_y, curr_y],
                color=COLOR_PERFIL_HEADER, linewidth=2.0,
                transform=ax.transAxes, zorder=203)
    
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
    fig, ax = plt.subplots(figsize=(34, len(df) * 1.1 + 7 + extra_h), dpi=200)
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
    
    # Cores Grupos — mapeadas para gradientes premium
    C_LE_TOP = "#4FC3F7" # Azul LE
    C_LD_TOP = "#FFB74D" # Laranja LD
    C_SG_TOP = "#81C784" # Verde SG
    _GRAD_LAT = {
        C_LE_TOP: GRAD_PRESSAO,
        C_LD_TOP: GRAD_POTENCIAL,
        C_SG_TOP: GRAD_SCOUTS,
    }
    
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
        
        grad = _GRAD_LAT.get(color, (color, color))
        draw_gradient_rect(ax, x_start, top_header_y, width, top_header_h,
                           grad[0], grad[1], zorder=100)
        ax.add_patch(patches.Rectangle(
            (x_start, top_header_y), width, top_header_h,
            facecolor="none", edgecolor="white", linewidth=1,
            transform=ax.transAxes, zorder=102
        ))
        ax.text(x_start + width/2, top_header_y + top_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=15, transform=ax.transAxes, zorder=103)

    # === SUB HEADERS (Verdes: DE, PG, BAS...) ===
    # Left: [DE, DE] [PG, PG] [BAS, BAS] ...
    # Right is reversed instructions
    
    sub_groups = [
        # Left LE
        ("DESARMES", 0, 2), ("G + A", 2, 4), ("MÉD. BÁSICA", 4, 6),
        # Left LD
        ("DESARMES", 6, 8), ("G + A", 8, 10), ("MÉD. BÁSICA", 10, 12),
        # Left SG
        ("SG", 12, 14),

        ("MANDO", 14, 15),

        # Right SG
        ("SG", 15, 17),
        # Right LD (Reverse: MED, PG, DE)
        ("MÉD. BÁSICA", 17, 19), ("G + A", 19, 21), ("DESARMES", 21, 23),
        # Right LE (Reverse: MED, PG, DE)
        ("MÉD. BÁSICA", 23, 25), ("G + A", 25, 27), ("DESARMES", 27, 29),
    ]
    
    for label, start_idx, end_idx in sub_groups:
        x_start = start_x + sum(col_widths[:start_idx])
        width = sum(col_widths[start_idx:end_idx])
        
        if label != "MANDO":
            draw_gradient_rect(ax, x_start, super_header_y, width, super_header_h,
                               GRAD_SCOUTS[0], GRAD_SCOUTS[1], zorder=100)
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor="none", edgecolor="white", linewidth=1,
                transform=ax.transAxes, zorder=102
            ))
        else:
            ax.add_patch(patches.Rectangle(
                (x_start, super_header_y), width, super_header_h,
                facecolor=COLOR_TCC_GREEN, edgecolor="none", linewidth=0,
                transform=ax.transAxes, zorder=100
            ))
        ax.text(x_start + width/2, super_header_y + super_header_h/2, label,
                ha="center", va="center", color="white", weight="bold",
                fontsize=12.5, transform=ax.transAxes, zorder=103)

    # === DATA LABELS (COC/CDF...) ===
    data_labels_h = 0.062
    data_labels_y = super_header_y - data_labels_h
    COLOR_CINZA = "#E5E7EB"

    curr_x = start_x
    for i, col in enumerate(all_cols):
        if col == "MANDO":
            # Label especial MANDO (CASA . FORA)
            label = "CASA • FORA"
            bg_color = "white"
            fsize = 9
        else:
            # Prefix Logic
            prefix = col.split("_")[0] # COC, CDF, COF, CDC
            if prefix in ["COC", "COF"]:
                bg_color = COLOR_TCC_PINK
            else:
                bg_color = COLOR_CINZA
            label = PREFIX_LABELS.get(prefix, prefix)
            fsize = 7.0

        rect = patches.Rectangle(
            (curr_x, data_labels_y), col_widths[i], data_labels_h,
            facecolor=bg_color, edgecolor="none", linewidth=0,
            transform=ax.transAxes, zorder=50
        )
        ax.add_patch(rect)
        ax.text(curr_x + col_widths[i]/2, data_labels_y + data_labels_h/2, label,
                ha="center", va="center", color="black", weight="bold",
                fontsize=fsize, family="DejaVu Sans",
                multialignment="center", linespacing=1.6,
                transform=ax.transAxes, zorder=52)
        curr_x += col_widths[i]

    # Bordas Labels
    ax.plot([start_x, start_x + sum(col_widths)], [data_labels_y, data_labels_y], color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)
    
    for i in range(len(col_widths)+1):
        x_pos = start_x + sum(col_widths[:i])
        ax.plot([x_pos, x_pos], [data_labels_y, data_labels_y + data_labels_h], color='black', linewidth=0.5, transform=ax.transAxes, zorder=51)

    # === ROWS ===

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
