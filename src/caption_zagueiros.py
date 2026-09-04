"""
caption_zagueiros.py
====================
Gerador de legenda textual para a tabela de Zagueiros.

Quatro blocos independentes — o mesmo time pode aparecer em mais de um:
  🛡️ ZAGUEIROS PARA SG
  🧱 ZAGUEIROS PARA DESARMES
  🎯 ZAGUEIROS PARA FINALIZAÇÕES
  📈 ZAGUEIROS PARA MÉDIA BÁSICA

MÉD. PTS não entra na legenda (continua aparecendo apenas na tabela).

IMPORTANTE — dado setorial:
  A tabela representa o grupo de zagueiros do time, não um jogador individual.
  Usar sempre "Os zagueiros do/da..." — nunca "A zaga do..." nem "o zagueiro do...".

Prefixos das colunas:
  COC = produção própria do mandante jogando em casa
  CDF = cedido pelo visitante quando joga fora
  COF = produção própria do visitante jogando fora
  CDC = cedido pelo mandante quando joga em casa
"""

# ============================================================
# DICIONÁRIOS DE ARTIGOS
# ============================================================

_ARTIGOS = {
    "FLAMENGO":            "do Flamengo",
    "VASCO":               "do Vasco",
    "FLUMINENSE":          "do Fluminense",
    "BOTAFOGO":            "do Botafogo",
    "PALMEIRAS":           "do Palmeiras",
    "SANTOS":              "do Santos",
    "SÃO PAULO":           "do São Paulo",
    "SAO PAULO":           "do São Paulo",
    "CORINTHIANS":         "do Corinthians",
    "MIRASSOL":            "do Mirassol",
    "ATLÉTICO-MG":         "do Atlético-MG",
    "ATLETICO-MG":         "do Atlético-MG",
    "ATLÉTICO MG":         "do Atlético-MG",
    "ATLETICO MG":         "do Atlético-MG",
    "ATLÉTICO":            "do Atlético",
    "ATLETICO":            "do Atlético",
    "CRUZEIRO":            "do Cruzeiro",
    "GRÊMIO":              "do Grêmio",
    "GREMIO":              "do Grêmio",
    "INTERNACIONAL":       "do Internacional",
    "CORITIBA":            "do Coritiba",
    "BAHIA":               "do Bahia",
    "VITÓRIA":             "do Vitória",
    "VITORIA":             "do Vitória",
    "REMO":                "do Remo",
    "ATHLETICO-PR":        "do Athletico-PR",
    "ATHLETICO PR":        "do Athletico-PR",
    "ATHLETICO":           "do Athletico",
    "RED BULL BRAGANTINO": "do Red Bull Bragantino",
    "RB BRAGANTINO":       "do Red Bull Bragantino",
    "RBB":                 "do Red Bull Bragantino",
    "BRAGANTINO":          "do Bragantino",
    "CHAPECOENSE":         "da Chapecoense",
    "FORTALEZA":           "do Fortaleza",
    "SPORT":               "do Sport",
    "GOIÁS":               "do Goiás",
    "GOIAS":               "do Goiás",
    "CUIABÁ":              "do Cuiabá",
    "CUIABA":              "do Cuiabá",
    "CEARÁ":               "do Ceará",
    "CEARA":               "do Ceará",
    "JUVENTUDE":           "do Juventude",
    "AMERICA-MG":          "do América-MG",
    "AMERICA MG":          "do América-MG",
}


# ============================================================
# HELPERS GERAIS
# ============================================================

def _fmt_team(team: str) -> str:
    """Artigo de time: 'do Flamengo', 'da Chapecoense'."""
    return _ARTIGOS.get(team.upper().strip(), f"do {team.title()}")


def _safe(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


# ============================================================
# FORMATAÇÃO ESPECÍFICA
# ============================================================

def format_sg(n) -> str:
    """1 → '1 SG'  |  N → 'N SGs'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} SG" if n == 1 else f"{n} SGs"


def format_desarmes(n) -> str:
    """1 → '1 DESARME'  |  N → 'N DESARMES'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} DESARME" if n == 1 else f"{n} DESARMES"


def format_finalizacoes(n) -> str:
    """1 → '1 FINALIZAÇÃO'  |  N → 'N FINALIZAÇÕES'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} FINALIZAÇÃO" if n == 1 else f"{n} FINALIZAÇÕES"


def format_pontos(value) -> str:
    """2.7 → '2,7'  |  4.0 → '4,0'  (notação decimal brasileira, 1 casa)"""
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def round_1(value) -> float:
    """Arredonda para 1 casa decimal, alinhado com o display da tabela.

    Garante que comparações de limiar usem o mesmo valor visual exibido.
    Exemplo: 2.6999999999999997 → 2.7  (evita falso negativo em >= 2.7)
    """
    return float(f"{float(value):.1f}")


# ============================================================
# BOLD FACTORY
# ============================================================

def _make_bold(wrap):
    """Retorna função de negrito para o formato solicitado.

    wrap=None  → identidade (texto puro)
    wrap='**'  → Telegram Markdown v1 (**texto**)
    wrap='<b>' → HTML (<b>texto</b>)
    """
    if wrap == "**":
        return lambda t: f"**{t}**"
    if wrap == "<b>":
        return lambda t: f"<b>{t}</b>"
    return lambda t: t


# ============================================================
# CRITÉRIOS DE QUALIFICAÇÃO (seletivos)
# ============================================================

def _qualifies_sg(sg_t: float) -> bool:
    """True apenas se os zagueiros vieram pegando SG no recorte.

    Critério único: SG_TIME >= 2.
    """
    return sg_t >= 2


def _qualifies_des(des_t: float, des_c: float) -> bool:
    """True se os zagueiros passam nos critérios de DESARMES.

    1. Produção própria muito forte:    DES_TIME >= 12
    2. Cruzamento equilibrado forte:    DES_TIME >= 9  E DES_CED >= 9
    3. Adversário cede muito + base:    DES_TIME >= 8  E DES_CED >= 12
    """
    return des_t >= 9


def _qualifies_fin(fin_t: float, fin_c: float) -> bool:
    """True se os zagueiros passam nos critérios de FINALIZAÇÕES.

    1. Produção própria forte:          FIN_TIME >= 5
    2. Cruzamento equilibrado forte:    FIN_TIME >= 4  E FIN_CED >= 4
    3. Adversário cede muito + base:    FIN_TIME >= 3  E FIN_CED >= 7
    """
    return False


def _qualifies_bas(bas_t: float, bas_c: float) -> bool:
    """True se os zagueiros passam nos critérios de MÉDIA BÁSICA.

    1. Produção própria forte:          BAS_TIME >= 2.7
    2. Cruzamento equilibrado forte:    BAS_TIME >= 2.4  E BAS_CED >= 2.4
    3. Adversário cede muito + base:    BAS_TIME >= 2.0  E BAS_CED >= 3.0

    Os limiares comparam valores arredondados a 1 casa decimal (round_1),
    alinhados com o display da tabela — evita falsos negativos por
    imprecisão de ponto flutuante (ex: 2.6999...97 exibido como 2,7).
    """
    t = round_1(bas_t)
    c = round_1(bas_c)
    return False


# ============================================================
# CONSTRUTORES DE FRASE
# ============================================================

def _sentence_sg(
    article: str,
    sg_t: int,
    mando_txt: str,
    wrap,
) -> str:
    b        = _make_bold(wrap)
    nome     = b(f"Os zagueiros {article}")
    sg_t_fmt = b(format_sg(sg_t))

    return (
        f"{nome} pegaram {sg_t_fmt} nos últimos 3 jogos {mando_txt}."
    )


def _sentence_des(
    article: str,
    des_t: int,
    des_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os zagueiros {article}")
    des_t_fmt = b(format_desarmes(des_t))
    des_c_fmt = b(format_desarmes(des_c))

    # Produção própria como único driver (des_c não alcança limiar cruzamento)
    if des_t >= 12 and des_c < 9:
        return (
            f"{nome} somaram {des_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento: adversário também é fator relevante
    return (
        f"{nome} somaram {des_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {des_c_fmt} para zagueiros rivais."
    )


def _sentence_fin(
    article: str,
    jogador: str,
    fin_t: int,
    fin_c: int,
    mando_txt: str,
    window_n: int,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(jogador.title()) if jogador else b(f"Um zagueiro {article}")
    fin_t_fmt = b(format_finalizacoes(fin_t))
    fin_c_fmt = b(format_finalizacoes(fin_c))

    # Produção própria como único driver (fin_c não alcança limiar cruzamento)
    if fin_c < 3 * max(window_n, 1) / 3:
        return (
            f"{nome} fez {fin_t_fmt} nos últimos {window_n} jogos {mando_txt}."
        )
    # Cruzamento: adversário também é fator relevante
    return (
        f"{nome} fez {fin_t_fmt} nos últimos {window_n} jogos {mando_txt}. "
        f"O adversário cedeu até {fin_c_fmt} a um mesmo zagueiro."
    )


def _sentence_bas(
    article: str,
    bas_t: float,
    bas_c: float,
    mando_txt: str,
    window_n: int,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os zagueiros {article}")
    bas_t_fmt = b(f"{format_pontos(bas_t)} PONTOS")
    bas_c_fmt = b(f"{format_pontos(bas_c)} PONTOS")

    # Usar round_1 na decisão de frase — mesmo arredondamento do filtro
    t = round_1(bas_t)
    c = round_1(bas_c)

    # Produção própria como único driver (bas_c não alcança limiar cruzamento)
    if t >= 2.7 and c < 2.4:
        return (
            f"{nome} têm média básica de {bas_t_fmt} nos últimos {window_n} jogos {mando_txt}."
        )
    # Cruzamento: adversário também é fator relevante
    return (
        f"{nome} têm média básica de {bas_t_fmt}, "
        f"e o adversário cedeu média de {bas_c_fmt} para zagueiros rivais."
    )


# ============================================================
# COLETA DE CANDIDATOS
# ============================================================

# (equipe_key, col_sg_t, col_sg_c, col_des_t, col_des_c, col_fin_t, col_fin_c, col_bas_t, col_bas_c)
_POSICOES = [
    ("MANDANTE", "COC_SG", "CDF_SG", "COC_DE", "CDF_DE", "COC_CHUTES_INDIV", "CDF_CHUTES_INDIV", "COC_CHUTES_JOGADOR", "COC_BASICA", "CDF_BASICA"),
    ("VISITANTE", "COF_SG", "CDC_SG", "COF_DE", "CDC_DE", "COF_CHUTES_INDIV", "CDC_CHUTES_INDIV", "COF_CHUTES_JOGADOR", "COF_BASICA", "CDC_BASICA"),
]


def _collect_candidates(rows: list, window_n: int = 3) -> dict:
    """Percorre todas as linhas e separa candidatos por bloco.

    Retorna {'sg': [...], 'des': [...], 'fin': [...], 'bas': [...]}.
    A ordem preserva a sequência dos jogos na tabela.
    Dentro do mesmo jogo: mandante primeiro, depois visitante.
    """
    sg_list, des_list, fin_list, bas_list = [], [], [], []

    for row in rows:
        man = str(row.get("MANDANTE", "")).strip()
        vis = str(row.get("VISITANTE", "")).strip()

        for (equipe_key, c_sg_t, c_sg_c, c_des_t, c_des_c, c_fin_t, c_fin_c, c_fin_player, c_bas_t, c_bas_c) in _POSICOES:
            time = man if equipe_key == "MANDANTE" else vis
            if not time:
                continue

            sg_t  = _safe(row, c_sg_t)
            sg_c  = _safe(row, c_sg_c)
            des_t = _safe(row, c_des_t)
            des_c = _safe(row, c_des_c)
            fin_t = _safe(row, c_fin_t)
            fin_c = _safe(row, c_fin_c)
            fin_leaders = row.get(f"DESTAQUES_{equipe_key}_CHUTES", []) or []
            fin_player = " / ".join(fin_leaders)
            bas_t = _safe(row, c_bas_t)
            bas_c = _safe(row, c_bas_c)

            entry = {
                "time":      time,
                "mando_txt": "em casa" if equipe_key == "MANDANTE" else "fora",
                "sg_t":  sg_t,  "sg_c":  sg_c,
                "des_t": des_t, "des_c": des_c,
                "fin_t": fin_t, "fin_c": fin_c,
                "fin_player": fin_player,
                "bas_t": bas_t, "bas_c": bas_c,
                "leaders": {
                    "des": row.get(f"DESTAQUES_{equipe_key}_DE", []) or [],
                    "fin": fin_leaders,
                    "bas": row.get(f"DESTAQUES_{equipe_key}_BASICA", []) or [],
                },
            }

            factor = max(window_n, 1) / 3
            if des_t >= 14 * factor or (des_t >= 11 * factor and des_c >= 11 * factor):
                des_list.append(entry)
            if fin_player and (fin_t >= 5 * factor or (fin_t >= 4 * factor and fin_c >= 4 * factor)):
                fin_list.append(entry)
            if round_1(bas_t) >= 3.5 or (round_1(bas_t) >= 3.1 and round_1(bas_c) >= 3.1):
                bas_list.append(entry)

    return {"sg": sg_list, "des": des_list, "fin": fin_list, "bas": bas_list}


# ============================================================
# GERADOR INTERNO — único para todos os formatos
# ============================================================

def _generate(rows: list, rodada: int, window_n: int, wrap=None) -> str:
    b          = _make_bold(wrap)
    candidates = _collect_candidates(rows, window_n)
    des_list   = candidates["des"]
    fin_list   = candidates["fin"]
    bas_list   = candidates["bas"]

    lines = [
        b("ANÁLISE ESTATÍSTICA — ZAGUEIROS"),
        "",
        f"Destaques positivos — últimos {window_n} jogos por mando.",
    ]

    if not des_list and not fin_list and not bas_list:
        lines += ["", "Nenhum grupo de zagueiros passou nos filtros de destaque positivo nesta rodada."]
        return "\n".join(lines)

    grouped = {}
    for scout, entries in (("des", des_list), ("fin", fin_list), ("bas", bas_list)):
        for e in entries:
            grouped.setdefault(e["time"], {"entry": e, "scouts": set()})["scouts"].add(scout)
    ranked = sorted(grouped.values(), key=lambda x: (
        "des" in x["scouts"], len(x["scouts"]), x["entry"]["des_t"],
        x["entry"]["bas_t"], x["entry"]["fin_t"]), reverse=True)[:5]
    lines += ["", b("🧱 DESTAQUES ENTRE OS ZAGUEIROS"), ""]
    for item in ranked:
        e, scouts = item["entry"], item["scouts"]
        subject = b(f"Os zagueiros {_fmt_team(e['time'])}")
        facts = []
        if "des" in scouts: facts.append(f"{int(e['des_t'])} desarmes")
        if "fin" in scouts: facts.append(f"{int(e['fin_t'])} finalizações do principal finalizador")
        if "bas" in scouts: facts.append(f"média básica de {format_pontos(e['bas_t'])} pontos")
        links = []
        labels = {"des": "desarmes", "fin": "finalizações", "bas": "pontuação básica"}
        for key in ("des", "fin", "bas"):
            if key in scouts and e["leaders"][key]: links.append(f"{labels[key]} — {b(' / '.join(e['leaders'][key]))}")
        suffix = f" Destaques individuais: {'; '.join(links)}." if links else ""
        lines.append(f"{subject}: {'; '.join(facts)} nos últimos {window_n} jogos {e['mando_txt']}.{suffix}")

    return "\n".join(lines)


# ============================================================
# API PÚBLICA
# ============================================================

def generate_zagueiros_caption(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em TEXTO PURO — sem marcadores, sem tags HTML."""
    return _generate(rows, rodada, window_n, wrap=None)


# Alias para consistência com outras posições
generate_zagueiros_caption_plain = generate_zagueiros_caption


def generate_zagueiros_caption_telegram_md(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em Telegram Markdown v1 — **negrito** nos termos-chave.

    Ao colar no Telegram Desktop e ENVIAR, os ** somem e o negrito aparece.
    Nunca usa escapes de MarkdownV2. Nunca gera barra invertida.
    """
    return _generate(rows, rodada, window_n, wrap="**")


def generate_zagueiros_caption_html(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em HTML com <b>...</b> — para preview no st.markdown."""
    return _generate(rows, rodada, window_n, wrap="<b>")


# Alias — para consistência com o padrão do app.py
generate_zagueiros_caption_for_clipboard = generate_zagueiros_caption_telegram_md
