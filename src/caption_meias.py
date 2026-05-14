"""
caption_meias.py
================
Gerador de legenda textual para a tabela de Meias.

Quatro blocos independentes — o mesmo time pode aparecer em mais de um:
  🧠 MEIAS PARA PASSE P/ FINALIZ.
  🚀 MEIAS PARA FINALIZAÇÕES
  ⚽ MEIAS PARA G + A
  📊 MEIAS PARA MÉDIA BÁSICA

IMPORTANTE — dado setorial:
  A tabela representa os meias de armação do time, não um jogador individual.
  Nunca usar "O meia do..." nem "Um meia do...".
  Usar sempre "Os meias de armação do/da...".

Prefixos das colunas:
  COC = conquistado pelo mandante em casa
  CDF = cedido pelo visitante quando joga fora
  COF = conquistado pelo visitante fora
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

def format_af(n) -> str:
    """1 → '1 PASSE P/ FINALIZ.'  |  N → 'N PASSES P/ FINALIZ.'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} PASSE P/ FINALIZ." if n == 1 else f"{n} PASSES P/ FINALIZ."


def format_finalizacoes(n) -> str:
    """1 → '1 FINALIZAÇÃO'  |  N → 'N FINALIZAÇÕES'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} FINALIZAÇÃO" if n == 1 else f"{n} FINALIZAÇÕES"


def format_pg(n) -> str:
    """1 → '1 PARTICIPAÇÃO EM GOL'  |  N → 'N PARTICIPAÇÕES EM GOL'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} PARTICIPAÇÃO EM GOL" if n == 1 else f"{n} PARTICIPAÇÕES EM GOL"


def format_pontos(value) -> str:
    """2.5 → '2,5'  |  3.0 → '3,0'  (notação decimal brasileira, 1 casa)"""
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def round_1(value) -> float:
    """Arredonda para 1 casa decimal — alinhado com o display da tabela.

    Evita falsos negativos por imprecisão de ponto flutuante
    (ex: 2.9999999999999996 exibido como 3,0 mas falhando >= 3.0).
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

def _qualifies_af(af_t: float, af_c: float) -> bool:
    """True se os meias de armação passam nos critérios de PASSE P/ FINALIZ.

    1. Produção própria forte:       AF_TIME >= 12
    2. Produção sólida + cedido alto: AF_TIME >= 10  E  AF_CED >= 12
    3. Base mínima + cedido muito alto: AF_TIME >= 9  E  AF_CED >= 15
    """
    return (
        af_t >= 12
        or (af_t >= 10 and af_c >= 12)
        or (af_t >= 9  and af_c >= 15)
    )


def _qualifies_fin(fin_t: float, fin_c: float) -> bool:
    """True se os meias de armação passam nos critérios de FINALIZAÇÕES.

    1. Produção própria forte:           FIN_TIME >= 9
    2. Produção sólida + cedido alto:    FIN_TIME >= 8  E  FIN_CED >= 10
    3. Base mínima + cedido muito alto:  FIN_TIME >= 7  E  FIN_CED >= 12

    Nota: FIN_TIME=7 e FIN_CED=7 NÃO entra — está abaixo do corte visual da tabela.
    """
    return (
        fin_t >= 9
        or (fin_t >= 8 and fin_c >= 10)
        or (fin_t >= 7 and fin_c >= 12)
    )


def _qualifies_pg(pg_t: float, pg_c: float, af_t: float, fin_t: float) -> bool:
    """True se os meias de armação passam nos critérios de G + A.

    1. Produção própria forte:                  PG_TIME >= 3
    2. Cruzamento com volume alto + contexto:   PG_TIME >= 2  E  PG_CED >= 3
                                                E (AF_TIME >= 9 OU FIN_TIME >= 7)

    Nota: PG_TIME=2 e PG_CED=2 NÃO entra — dado setorial exige adversário cedendo mais.
    """
    return (
        pg_t >= 3
        or (pg_t >= 2 and pg_c >= 3 and (af_t >= 9 or fin_t >= 7))
    )


def _qualifies_bas(bas_t: float, bas_c: float) -> bool:
    """True se os meias de armação passam nos critérios de MÉDIA BÁSICA.

    1. Produção própria forte:            BAS_TIME >= 3.0
    2. Produção sólida + cedido alto:     BAS_TIME >= 2.5  E  BAS_CED >= 3.0
    3. Base mínima + cedido muito alto:   BAS_TIME >= 2.4  E  BAS_CED >= 3.5

    Nota: BAS_TIME=2.0 e BAS_CED=3.0 NÃO entra — produção própria abaixo do limiar.
    Usa round_1 para alinhar com o display da tabela (evita float impreciso).
    """
    t = round_1(bas_t)
    c = round_1(bas_c)
    return (
        t >= 3.0
        or (t >= 2.5 and c >= 3.0)
        or (t >= 2.4 and c >= 3.5)
    )


# ============================================================
# CONSTRUTORES DE FRASE
# ============================================================

def _sentence_af(
    article: str,
    af_t: int,
    af_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b        = _make_bold(wrap)
    nome     = b(f"Os meias {article}")
    af_t_fmt = b(format_af(af_t))
    af_c_fmt = b(format_af(af_c))

    # Produção própria como único driver
    if af_t >= 12 and af_c < 10:
        return (
            f"{nome} somaram {af_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento: adversário também é fator
    return (
        f"{nome} somaram {af_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {af_c_fmt} para meias rivais."
    )


def _sentence_fin(
    article: str,
    fin_t: int,
    fin_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os meias {article}")
    fin_t_fmt = b(format_finalizacoes(fin_t))
    fin_c_fmt = b(format_finalizacoes(fin_c))

    # Produção própria como único driver
    if fin_t >= 9 and fin_c < 7:
        return (
            f"{nome} somaram {fin_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento
    return (
        f"{nome} somaram {fin_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {fin_c_fmt} para meias rivais."
    )


def _sentence_pg(
    article: str,
    pg_t: int,
    pg_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b        = _make_bold(wrap)
    nome     = b(f"Os meias {article}")
    pg_t_fmt = b(format_pg(pg_t))
    pg_c_fmt = b(format_pg(pg_c))

    # Produção própria como único driver
    if pg_t >= 3 and pg_c < 2:
        return (
            f"{nome} tiveram {pg_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento
    return (
        f"{nome} tiveram {pg_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {pg_c_fmt} para meias rivais."
    )


def _sentence_bas(
    article: str,
    bas_t: float,
    bas_c: float,
    mando_txt: str,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os meias {article}")
    bas_t_fmt = b(f"{format_pontos(bas_t)} PONTOS")
    bas_c_fmt = b(f"{format_pontos(bas_c)} PONTOS")

    # Usar round_1 na decisão de frase — alinhado com o filtro
    t = round_1(bas_t)
    c = round_1(bas_c)

    # Produção própria como único driver
    if t >= 3.0 and c < 2.5:
        return (
            f"{nome} têm média básica de {bas_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento
    return (
        f"{nome} têm média básica de {bas_t_fmt}, "
        f"e o adversário cedeu média de {bas_c_fmt} para meias rivais."
    )


# ============================================================
# COLETA DE CANDIDATOS
# ============================================================

# (equipe_key, col_af_t, col_af_c, col_fin_t, col_fin_c,
#              col_pg_t, col_pg_c, col_bas_t, col_bas_c)
_POSICOES = [
    ("MANDANTE",
     "COC_AF",    "CDF_AF",
     "COC_CHUTES","CDF_CHUTES",
     "COC_PG",    "CDF_PG",
     "COC_BASICA","CDF_BASICA"),
    ("VISITANTE",
     "COF_AF",    "CDC_AF",
     "COF_CHUTES","CDC_CHUTES",
     "COF_PG",    "CDC_PG",
     "COF_BASICA","CDC_BASICA"),
]


def _collect_candidates(rows: list) -> dict:
    """Percorre todas as linhas e separa candidatos por bloco.

    Retorna {'af': [...], 'fin': [...], 'pg': [...], 'bas': [...]}.
    Ordem: jogos da tabela; dentro do mesmo jogo, mandante antes do visitante.
    """
    af_list, fin_list, pg_list, bas_list = [], [], [], []

    for row in rows:
        man = str(row.get("MANDANTE", "")).strip()
        vis = str(row.get("VISITANTE", "")).strip()

        for (equipe_key,
             c_af_t,  c_af_c,
             c_fin_t, c_fin_c,
             c_pg_t,  c_pg_c,
             c_bas_t, c_bas_c) in _POSICOES:

            time = man if equipe_key == "MANDANTE" else vis
            if not time:
                continue

            af_t  = _safe(row, c_af_t)
            af_c  = _safe(row, c_af_c)
            fin_t = _safe(row, c_fin_t)
            fin_c = _safe(row, c_fin_c)
            pg_t  = _safe(row, c_pg_t)
            pg_c  = _safe(row, c_pg_c)
            bas_t = _safe(row, c_bas_t)
            bas_c = _safe(row, c_bas_c)

            entry = {
                "time":      time,
                "mando_txt": "em casa" if equipe_key == "MANDANTE" else "fora",
                "af_t":  af_t,  "af_c":  af_c,
                "fin_t": fin_t, "fin_c": fin_c,
                "pg_t":  pg_t,  "pg_c":  pg_c,
                "bas_t": bas_t, "bas_c": bas_c,
            }

            if _qualifies_af(af_t, af_c):
                af_list.append(entry)
            if _qualifies_fin(fin_t, fin_c):
                fin_list.append(entry)
            if _qualifies_pg(pg_t, pg_c, af_t, fin_t):
                pg_list.append(entry)
            if _qualifies_bas(bas_t, bas_c):
                bas_list.append(entry)

    return {"af": af_list, "fin": fin_list, "pg": pg_list, "bas": bas_list}


# ============================================================
# GERADOR INTERNO — único para todos os formatos
# ============================================================

def _generate(rows: list, rodada: int, window_n: int, wrap=None) -> str:
    b          = _make_bold(wrap)
    candidates = _collect_candidates(rows)
    af_list    = candidates["af"]
    fin_list   = candidates["fin"]
    pg_list    = candidates["pg"]
    bas_list   = candidates["bas"]

    lines = [
        b("ANÁLISE ESTATÍSTICA — MEIAS"),
        "",
        f"Destaques positivos — últimos {window_n} jogos por mando.",
    ]

    if not af_list and not fin_list and not pg_list and not bas_list:
        lines += [
            "",
            "Nenhum grupo de meias passou nos filtros de destaque positivo nesta rodada.",
        ]
        return "\n".join(lines)

    def _bloco(titulo: str, entradas: list, builder) -> list:
        bloco = ["", b(titulo), ""]
        for e in entradas:
            article = _fmt_team(e["time"])
            frase   = builder(e, article, wrap)
            if frase:
                bloco.append(frase)
                bloco.append("")
        while bloco and bloco[-1] == "":
            bloco.pop()
        return bloco

    def _build_af(e, article, wrap):
        return _sentence_af(article, int(e["af_t"]), int(e["af_c"]), e["mando_txt"], wrap)

    def _build_fin(e, article, wrap):
        return _sentence_fin(article, int(e["fin_t"]), int(e["fin_c"]), e["mando_txt"], wrap)

    def _build_pg(e, article, wrap):
        return _sentence_pg(article, int(e["pg_t"]), int(e["pg_c"]), e["mando_txt"], wrap)

    def _build_bas(e, article, wrap):
        return _sentence_bas(article, e["bas_t"], e["bas_c"], e["mando_txt"], wrap)

    if af_list:
        lines += _bloco("🧠 MEIAS PARA PASSE P/ FINALIZ.", af_list, _build_af)
    if fin_list:
        lines += _bloco("🚀 MEIAS PARA FINALIZAÇÕES", fin_list, _build_fin)
    if pg_list:
        lines += _bloco("⚽ MEIAS PARA G + A", pg_list, _build_pg)
    if bas_list:
        lines += _bloco("📊 MEIAS PARA MÉDIA BÁSICA", bas_list, _build_bas)

    return "\n".join(lines)


# ============================================================
# API PÚBLICA
# ============================================================

def generate_meias_caption(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em TEXTO PURO — sem marcadores, sem tags HTML."""
    return _generate(rows, rodada, window_n, wrap=None)


generate_meias_caption_plain = generate_meias_caption


def generate_meias_caption_telegram_md(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em Telegram Markdown v1 — **negrito** nos termos-chave."""
    return _generate(rows, rodada, window_n, wrap="**")


def generate_meias_caption_html(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em HTML com <b>...</b> — para preview no st.markdown."""
    return _generate(rows, rodada, window_n, wrap="<b>")


generate_meias_caption_for_clipboard = generate_meias_caption_telegram_md
