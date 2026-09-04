"""caption_atacantes.py
====================
Gerador de legenda textual para a tabela de Atacantes.

Três blocos independentes — o mesmo time pode aparecer em mais de um:
  🚀 ATACANTES PARA FINALIZAÇÕES
  ⚽ ATACANTES PARA G + A
  📊 ATACANTES PARA MÉDIA BÁSICA

NOTA: PASSE FIN. não entra na legenda — é pré-scout.

IMPORTANTE — dado setorial:
  A tabela representa todos os atacantes do time nos jogos do recorte,
  não um jogador individual.
  Nunca usar "O atacante do..." nem "Um atacante do...".
  Usar sempre "Os atacantes do/da...".

Prefixos das colunas:
  COC = conquistado pelo mandante em casa
  CDF = cedido pelo visitante quando joga fora
  COF = conquistado pelo visitante fora
  CDC = cedido pelo mandante quando joga em casa
"""

from .calibration import caption_qualifies
from .cartola_lineups import safe_names

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
# CONSTRUTORES DE FRASE
# ============================================================

def _sentence_fin(
    article: str,
    fin_t: int,
    fin_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os atacantes {article}")
    fin_t_fmt = b(format_finalizacoes(fin_t))
    fin_c_fmt = b(format_finalizacoes(fin_c))

    # Produção própria como único driver
    if fin_t >= 18 and fin_c < 12:
        return (
            f"{nome} somaram {fin_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento: adversário também é fator
    return (
        f"{nome} somaram {fin_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {fin_c_fmt} para atacantes rivais."
    )


def _sentence_pg(
    article: str,
    pg_t: int,
    pg_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b        = _make_bold(wrap)
    nome     = b(f"Os atacantes {article}")
    pg_t_fmt = b(format_pg(pg_t))
    pg_c_fmt = b(format_pg(pg_c))

    # Produção própria como único driver
    if pg_t >= 5 and pg_c < 3:
        return (
            f"{nome} tiveram {pg_t_fmt} nos últimos 3 jogos {mando_txt}."
        )
    # Cruzamento
    return (
        f"{nome} tiveram {pg_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {pg_c_fmt} para atacantes rivais."
    )


def _sentence_bas(
    article: str,
    bas_t: float,
    bas_c: float,
    mando_txt: str,
    wrap,
) -> str:
    b         = _make_bold(wrap)
    nome      = b(f"Os atacantes {article}")
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
        f"e o adversário cedeu média de {bas_c_fmt} para atacantes rivais."
    )


# ============================================================
# COLETA DE CANDIDATOS
# ============================================================

# (equipe_key, col_fin_t, col_fin_c, col_pg_t, col_pg_c, col_bas_t, col_bas_c)
_POSICOES = [
    ("MANDANTE",
     "COC_CHUTES", "CDF_CHUTES",
     "COC_PG",     "CDF_PG",
     "COC_BASICA", "CDF_BASICA"),
    ("VISITANTE",
     "COF_CHUTES", "CDC_CHUTES",
     "COF_PG",     "CDC_PG",
     "COF_BASICA", "CDC_BASICA"),
]


def _collect_candidates(rows: list, window_n: int = 3) -> dict:
    """Percorre todas as linhas e separa candidatos por bloco.

    Retorna {'fin': [...], 'pg': [...], 'bas': [...]}.
    Ordem: jogos da tabela; dentro do mesmo jogo, mandante antes do visitante.
    """
    fin_list, pg_list, bas_list = [], [], []

    for row in rows:
        man = str(row.get("MANDANTE", "")).strip()
        vis = str(row.get("VISITANTE", "")).strip()

        for (equipe_key,
             c_fin_t, c_fin_c,
             c_pg_t,  c_pg_c,
             c_bas_t, c_bas_c) in _POSICOES:

            time = man if equipe_key == "MANDANTE" else vis
            if not time:
                continue

            fin_t = _safe(row, c_fin_t)
            fin_c = _safe(row, c_fin_c)
            pg_t  = _safe(row, c_pg_t)
            pg_c  = _safe(row, c_pg_c)
            bas_t = _safe(row, c_bas_t)
            bas_c = _safe(row, c_bas_c)

            entry = {
                "time":      time,
                "mando_txt": "em casa" if equipe_key == "MANDANTE" else "fora",
                "fin_t": fin_t, "fin_c": fin_c,
                "pg_t":  pg_t,  "pg_c":  pg_c,
                "g_t": _safe(row, f"{'COC' if equipe_key == 'MANDANTE' else 'COF'}_G"),
                "a_t": _safe(row, f"{'COC' if equipe_key == 'MANDANTE' else 'COF'}_A"),
                "bas_t": bas_t, "bas_c": bas_c,
                "leaders": {
                    "g": safe_names(row.get(f"DESTAQUES_{equipe_key}_G")),
                    "a": safe_names(row.get(f"DESTAQUES_{equipe_key}_A")),
                    "pg": safe_names(row.get(f"DESTAQUES_{equipe_key}_PG")),
                    "fin": safe_names(row.get(f"DESTAQUES_{equipe_key}_CHUTES")),
                    "bas": safe_names(row.get(f"DESTAQUES_{equipe_key}_BASICA")),
                },
            }

            if caption_qualifies("ATACANTES", "CHUTES", fin_t, fin_c, window_n):
                fin_list.append(entry)
            if caption_qualifies("ATACANTES", "PG", pg_t, pg_c, window_n, {"CHUTES": fin_t}):
                pg_list.append(entry)
            if caption_qualifies("ATACANTES", "BASICA", bas_t, bas_c, window_n):
                bas_list.append(entry)

    return {"fin": fin_list, "pg": pg_list, "bas": bas_list}


# ============================================================
# GERADOR INTERNO — único para todos os formatos
# ============================================================

def _generate(rows: list, rodada: int, window_n: int, wrap=None) -> str:
    b          = _make_bold(wrap)
    candidates = _collect_candidates(rows, window_n)
    fin_list   = candidates["fin"]
    pg_list    = candidates["pg"]
    bas_list   = candidates["bas"]
    lines = [
        b("ANÁLISE ESTATÍSTICA: ATACANTES"),
        "",
        f"Destaques positivos nos últimos {window_n} jogos por mando.",
    ]

    if not fin_list and not pg_list and not bas_list:
        lines += [
            "",
            "Nenhum grupo de atacantes passou nos filtros de destaque positivo nesta rodada.",
        ]
        return "\n".join(lines)

    grouped = {}
    for scout, entries in (("pg", pg_list), ("fin", fin_list), ("bas", bas_list)):
        for entry in entries:
            grouped.setdefault(entry["time"], {"entry": entry, "scouts": set()})["scouts"].add(scout)
    ranked = sorted(grouped.values(), key=lambda x: (
        "pg" in x["scouts"], x["entry"]["g_t"], len(x["scouts"]), x["entry"]["pg_t"],
        x["entry"]["fin_t"], x["entry"]["bas_t"]), reverse=True)[:5]
    lines += ["", b("⚽ DESTAQUES ENTRE OS ATACANTES"), ""]
    for item in ranked:
        e, scouts = item["entry"], item["scouts"]
        leaders = e["leaders"]
        subject = b(f"Os atacantes {_fmt_team(e['time'])}")
        facts = []
        if "pg" in scouts:
            if e["g_t"] > 0:
                goals = f"{int(e['g_t'])} gol" if int(e["g_t"]) == 1 else f"{int(e['g_t'])} gols"
                assists = f" e {int(e['a_t'])} assistência" if e["a_t"] == 1 else (f" e {int(e['a_t'])} assistências" if e["a_t"] else "")
                facts.append(f"marcaram {b(goals + assists)}")
            else:
                facts.append(f"somaram {b(format_pg(e['pg_t']).lower())}")
        if "fin" in scouts:
            facts.append(f"fizeram {b(format_finalizacoes(e['fin_t']).lower())}")
        if "bas" in scouts:
            facts.append(f"tiveram média básica de {b(format_pontos(e['bas_t']) + ' pontos')}")
        links = []
        if "pg" in scouts and leaders["g"]: links.append(f"gols: {b(' / '.join(leaders['g']))}")
        if "pg" in scouts and leaders["a"]: links.append(f"assistências: {b(' / '.join(leaders['a']))}")
        if "fin" in scouts and leaders["fin"]: links.append(f"finalizações: {b(' / '.join(leaders['fin']))}")
        if "bas" in scouts and leaders["bas"]: links.append(f"pontuação básica: {b(' / '.join(leaders['bas']))}")
        suffix = f" Destaques individuais: {'; '.join(links)}." if links else ""
        lines.append(f"{subject}: {' e '.join(facts)} nos últimos {window_n} jogos {e['mando_txt']}.{suffix}")

    return "\n".join(lines)


# ============================================================
# API PÚBLICA
# ============================================================

def generate_atacantes_caption(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em TEXTO PURO — sem marcadores, sem tags HTML."""
    return _generate(rows, rodada, window_n, wrap=None)


generate_atacantes_caption_plain = generate_atacantes_caption


def generate_atacantes_caption_telegram_md(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em Telegram Markdown v1 — **negrito** nos termos-chave."""
    return _generate(rows, rodada, window_n, wrap="**")


def generate_atacantes_caption_html(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em HTML com <b>...</b> — para preview no st.markdown."""
    return _generate(rows, rodada, window_n, wrap="<b>")


generate_atacantes_caption_for_clipboard = generate_atacantes_caption_telegram_md
