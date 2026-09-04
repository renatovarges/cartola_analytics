"""caption_laterais.py
===================
Gerador de legenda textual para a tabela de Laterais.

Três blocos independentes — o mesmo lateral pode aparecer em mais de um:
  🧱 LATERAIS PARA DESARMES
  📊 LATERAIS PARA MÉD. BÁSICA
  🎯 LATERAIS PARA G + A

SG não entra na legenda (continua aparecendo apenas na tabela).

Formatos via `wrap`:
  wrap=None  → texto puro (sem marcadores)
  wrap='**'  → Telegram Markdown v1 (**negrito** — sem escapes)
  wrap='<b>' → HTML com <b>...</b>

Colunas do engine (prefixos COC/CDF/COF/CDC + posição + scout):
  COC = produção própria do mandante jogando em casa
  CDF = cedido pelo visitante quando joga fora
  COF = produção própria do visitante jogando fora
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

# Lado → texto singular e plural
_LADO_TXT    = {"LE": "esquerdo", "LD": "direito"}
_LADO_PLURAL = {"LE": "laterais esquerdos", "LD": "laterais direitos"}


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


def round_1(value) -> float:
    return float(f"{float(value):.1f}")


# ============================================================
# FORMATAÇÃO ESPECÍFICA
# ============================================================

def format_desarmes(n) -> str:
    """1 → '1 desarme'  |  N → 'N desarmes'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} desarme" if n == 1 else f"{n} desarmes"


def format_pontos_media(value) -> str:
    """3.9 → '3,9'  |  4.0 → '4,0'  (notação decimal brasileira, 1 casa)"""
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def format_ga_time(n) -> str:
    """1 → '1 gol'  |  N → 'N gols'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} gol" if n == 1 else f"{n} gols"


def format_ga_ced(n) -> str:
    """1 → '1 participação em gol'  |  N → 'N participações em gol'"""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return "1 participação em gol" if n == 1 else f"{n} participações em gol"


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

def _sentence_desarmes(
    article: str,
    lado: str,
    des_t: int,
    des_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b           = _make_bold(wrap)
    nome        = b(f"O lateral {_LADO_TXT[lado]} {article}")
    lado_plural = _LADO_PLURAL[lado]
    des_t_fmt   = b(format_desarmes(des_t).upper())
    des_c_fmt   = b(format_desarmes(des_c).upper())

    if des_t >= 10 and des_c < 8:
        return f"{nome} somou {des_t_fmt} nos últimos 3 jogos {mando_txt}."
    # des_t>=8 e des_c>=8  |  des_c>=10 e des_t>=7
    return (
        f"{nome} somou {des_t_fmt} nos últimos 3 jogos {mando_txt}, "
        f"e o adversário cedeu {des_c_fmt} para {lado_plural} rivais."
    )


def _sentence_bas(
    article: str,
    lado: str,
    bas_t: float,
    bas_c: float,
    mando_txt: str,
    wrap,
) -> str:
    b           = _make_bold(wrap)
    nome        = b(f"O lateral {_LADO_TXT[lado]} {article}")
    lado_plural = _LADO_PLURAL[lado]
    bas_t_fmt   = b(f"{format_pontos_media(bas_t)} PONTOS")
    bas_c_fmt   = b(f"{format_pontos_media(bas_c)} PONTOS")

    if bas_t >= 4.0 and bas_c < 3.5:
        return f"{nome} tem média básica de {bas_t_fmt} nos últimos 3 jogos {mando_txt}."
    # bas_t>=3.5 e bas_c>=3.5  |  bas_c>=4.0 e bas_t>=3.3  |  cruzamento
    return (
        f"{nome} tem média básica de {bas_t_fmt}, "
        f"e o adversário cedeu média de {bas_c_fmt} para {lado_plural} rivais."
    )


def _sentence_ga(
    article: str,
    lado: str,
    ga_t: int,
    ga_c: int,
    mando_txt: str,
    wrap,
) -> str:
    b           = _make_bold(wrap)
    nome        = b(f"O lateral {_LADO_TXT[lado]} {article}")
    lado_plural = _LADO_PLURAL[lado]
    # Ambos os lados usam "participação/participações em gol" em CAIXA ALTA
    ga_t_fmt    = b(format_ga_ced(ga_t).upper())
    ga_c_fmt    = b(format_ga_ced(ga_c).upper())

    if ga_t >= 1 and ga_c >= 1:
        return (
            f"{nome} teve {ga_t_fmt} nos últimos 3 jogos {mando_txt}, "
            f"e o adversário cedeu {ga_c_fmt} para {lado_plural} rivais."
        )
    # ga_t >= 2 e ga_c == 0 — produção própria
    return f"{nome} teve {ga_t_fmt} nos últimos 3 jogos {mando_txt}."


# ============================================================
# COLETA DE CANDIDATOS
# ============================================================

# (time, lado, mando, col_des_t, col_des_c, col_ga_t, col_ga_c, col_bas_t, col_bas_c)
_POSICOES = [
    ("MANDANTE", "LE", "COC_LE_DE", "CDF_LE_DE", "COC_LE_PG", "CDF_LE_PG", "COC_LE_BAS", "CDF_LE_BAS"),
    ("MANDANTE", "LD", "COC_LD_DE", "CDF_LD_DE", "COC_LD_PG", "CDF_LD_PG", "COC_LD_BAS", "CDF_LD_BAS"),
    ("VISITANTE", "LE", "COF_LE_DE", "CDC_LE_DE", "COF_LE_PG", "CDC_LE_PG", "COF_LE_BAS", "CDC_LE_BAS"),
    ("VISITANTE", "LD", "COF_LD_DE", "CDC_LD_DE", "COF_LD_PG", "CDC_LD_PG", "COF_LD_BAS", "CDC_LD_BAS"),
]


def _collect_candidates(rows: list, window_n: int = 3) -> dict:
    """Percorre todas as linhas e separa candidatos por bloco.

    Retorna {'des': [...], 'bas': [...], 'ga': [...]}.
    A ordem preserva a sequência dos jogos na tabela.
    Dentro do mesmo jogo: mandante LE → mandante LD → visitante LE → visitante LD.
    """
    des_list, bas_list, ga_list = [], [], []

    for row in rows:
        man = str(row.get("MANDANTE", "")).strip()
        vis = str(row.get("VISITANTE", "")).strip()

        for (equipe_key, lado, c_des_t, c_des_c, c_ga_t, c_ga_c, c_bas_t, c_bas_c) in _POSICOES:
            time = man if equipe_key == "MANDANTE" else vis
            if not time:
                continue

            des_t = _safe(row, c_des_t)
            des_c = _safe(row, c_des_c)
            ga_t  = _safe(row, c_ga_t)
            ga_c  = _safe(row, c_ga_c)
            bas_t = _safe(row, c_bas_t)
            bas_c = _safe(row, c_bas_c)

            entry = {
                "time":      time,
                "lado":      lado,
                "mando_txt": "em casa" if equipe_key == "MANDANTE" else "fora",
                "des_t": des_t, "des_c": des_c,
                "ga_t":  ga_t,  "ga_c":  ga_c,
                "bas_t": bas_t, "bas_c": bas_c,
                "leaders": {
                    "des": safe_names(row.get(f"DESTAQUES_{equipe_key}_{lado}_DE")),
                    "bas": safe_names(row.get(f"DESTAQUES_{equipe_key}_{lado}_BASICA")),
                    "ga": safe_names(row.get(f"DESTAQUES_{equipe_key}_{lado}_PG")),
                },
            }

            if caption_qualifies("LATERAIS", "DE", des_t, des_c, window_n):
                des_list.append(entry)
            if caption_qualifies("LATERAIS", "BASICA", bas_t, bas_c, window_n):
                bas_list.append(entry)
            if caption_qualifies("LATERAIS", "PG", ga_t, ga_c, window_n):
                ga_list.append(entry)

    return {"des": des_list, "bas": bas_list, "ga": ga_list}


# ============================================================
# GERADOR INTERNO — único para todos os formatos
# ============================================================

def _generate(rows: list, rodada: int, window_n: int, wrap=None) -> str:
    b          = _make_bold(wrap)
    candidates = _collect_candidates(rows, window_n)
    des_list   = candidates["des"]
    bas_list   = candidates["bas"]
    ga_list    = candidates["ga"]

    lines = [
        b("ANÁLISE ESTATÍSTICA — LATERAIS"),
        "",
        f"Destaques positivos — últimos {window_n} jogos por mando.",
    ]

    if not des_list and not bas_list and not ga_list:
        lines += ["", "Nenhum lateral passou nos filtros de destaque positivo nesta rodada."]
        return "\n".join(lines)

    grouped = {}
    for scout, entries in (("des", des_list), ("bas", bas_list), ("ga", ga_list)):
        for e in entries:
            item = grouped.setdefault(e["time"], {"entry": e, "scouts": set(), "best": {}})
            item["scouts"].add(scout)
            metric = {"des": "des_t", "bas": "bas_t", "ga": "ga_t"}[scout]
            if scout not in item["best"] or e[metric] > item["best"][scout][metric]:
                item["best"][scout] = e
    ranked = sorted(grouped.values(), key=lambda x: (
        "des" in x["scouts"], "bas" in x["scouts"], len(x["scouts"]),
        x["best"].get("des", x["entry"])["des_t"]), reverse=True)[:5]
    lines += ["", b("🧱 DESTAQUES ENTRE OS LATERAIS"), ""]
    for item in ranked:
        e, scouts = item["entry"], item["scouts"]
        names = []
        for key in ("des", "bas", "ga"):
            for name in item["best"].get(key, e)["leaders"][key]:
                if name not in names: names.append(name)
        subject = b(f"Os laterais {_fmt_team(e['time'])}")
        facts = []
        if "des" in scouts: facts.append(f"{int(item['best']['des']['des_t'])} desarmes")
        if "bas" in scouts: facts.append(f"média básica de {format_pontos_media(item['best']['bas']['bas_t'])} pontos")
        if "ga" in scouts: facts.append(f"{int(item['best']['ga']['ga_t'])} participações em gol")
        links = []
        labels = {"des": "desarmes", "bas": "pontuação básica", "ga": "G + A"}
        for key in ("des", "bas", "ga"):
            linked = item["best"].get(key, e)["leaders"][key]
            if key in scouts and linked: links.append(f"{labels[key]} — {b(' / '.join(linked))}")
        suffix = f" Destaques individuais: {'; '.join(links)}." if links else ""
        lines.append(f"{subject}: {'; '.join(facts)} nos últimos {window_n} jogos {e['mando_txt']}.{suffix}")

    return "\n".join(lines)


# ============================================================
# API PÚBLICA
# ============================================================

def generate_laterais_caption(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em TEXTO PURO — sem marcadores, sem tags HTML."""
    return _generate(rows, rodada, window_n, wrap=None)


# Alias para consistência com caption_goleiros
generate_laterais_caption_plain = generate_laterais_caption


def generate_laterais_caption_telegram_md(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em Telegram Markdown v1 — **negrito** nos termos-chave.

    Ao colar no Telegram Desktop e ENVIAR, os ** somem e o negrito aparece.
    Nunca usa escapes de MarkdownV2. Nunca gera barra invertida.
    """
    return _generate(rows, rodada, window_n, wrap="**")


def generate_laterais_caption_html(
    rows: list,
    rodada: int,
    window_n: int = 3,
) -> str:
    """Legenda em HTML com <b>...</b> — para preview no st.markdown."""
    return _generate(rows, rodada, window_n, wrap="<b>")


# Alias — para consistência com o padrão do app.py
generate_laterais_caption_for_clipboard = generate_laterais_caption_telegram_md
