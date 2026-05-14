"""
caption_goleiros.py
===================
Gerador de legenda textual para a tabela de Goleiros.

Formatos disponíveis via parâmetro `wrap`:
  wrap=None  → texto puro (sem marcadores)
  wrap='**'  → Telegram Markdown v1 (**negrito** — sem escapes)
  wrap='<b>' → HTML com <b>...</b>

Regras de negócio:
- Somente perfis positivos: SG+DE, SG, DE
- BOMB / - / vazio → ignorado
- Ordenação: SG+DE → SG → DE; dentro do grupo, ordem de inserção (estável)
- Máximo de 6 destaques por legenda
- Nunca usar barra invertida. Nunca gerar 'SG \\+ DEFESAS'.
"""

# ============================================================
# DICIONÁRIOS DE NOMES E ARTIGOS
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

_NOMES = {
    "FLAMENGO":            "Flamengo",
    "VASCO":               "Vasco",
    "FLUMINENSE":          "Fluminense",
    "BOTAFOGO":            "Botafogo",
    "PALMEIRAS":           "Palmeiras",
    "SANTOS":              "Santos",
    "SÃO PAULO":           "São Paulo",
    "SAO PAULO":           "São Paulo",
    "CORINTHIANS":         "Corinthians",
    "MIRASSOL":            "Mirassol",
    "ATLÉTICO-MG":         "Atlético-MG",
    "ATLETICO-MG":         "Atlético-MG",
    "ATLÉTICO MG":         "Atlético-MG",
    "ATLETICO MG":         "Atlético-MG",
    "ATLÉTICO":            "Atlético",
    "ATLETICO":            "Atlético",
    "CRUZEIRO":            "Cruzeiro",
    "GRÊMIO":              "Grêmio",
    "GREMIO":              "Grêmio",
    "INTERNACIONAL":       "Internacional",
    "CORITIBA":            "Coritiba",
    "BAHIA":               "Bahia",
    "VITÓRIA":             "Vitória",
    "VITORIA":             "Vitória",
    "REMO":                "Remo",
    "ATHLETICO-PR":        "Athletico-PR",
    "ATHLETICO PR":        "Athletico-PR",
    "ATHLETICO":           "Athletico",
    "RED BULL BRAGANTINO": "Red Bull Bragantino",
    "RB BRAGANTINO":       "Red Bull Bragantino",
    "RBB":                 "Red Bull Bragantino",
    "BRAGANTINO":          "Bragantino",
    "CHAPECOENSE":         "Chapecoense",
    "FORTALEZA":           "Fortaleza",
    "SPORT":               "Sport",
    "GOIÁS":               "Goiás",
    "GOIAS":               "Goiás",
    "CUIABÁ":              "Cuiabá",
    "CUIABA":              "Cuiabá",
    "CEARÁ":               "Ceará",
    "CEARA":               "Ceará",
    "JUVENTUDE":           "Juventude",
    "AMERICA-MG":          "América-MG",
    "AMERICA MG":          "América-MG",
}

_ARTIGOS_SUJEITO = {
    "FLAMENGO":            "O Flamengo",
    "VASCO":               "O Vasco",
    "FLUMINENSE":          "O Fluminense",
    "BOTAFOGO":            "O Botafogo",
    "PALMEIRAS":           "O Palmeiras",
    "SANTOS":              "O Santos",
    "SÃO PAULO":           "O São Paulo",
    "SAO PAULO":           "O São Paulo",
    "CORINTHIANS":         "O Corinthians",
    "MIRASSOL":            "O Mirassol",
    "ATLÉTICO-MG":         "O Atlético-MG",
    "ATLETICO-MG":         "O Atlético-MG",
    "ATLÉTICO MG":         "O Atlético-MG",
    "ATLETICO MG":         "O Atlético-MG",
    "ATLÉTICO":            "O Atlético",
    "ATLETICO":            "O Atlético",
    "CRUZEIRO":            "O Cruzeiro",
    "GRÊMIO":              "O Grêmio",
    "GREMIO":              "O Grêmio",
    "INTERNACIONAL":       "O Internacional",
    "CORITIBA":            "O Coritiba",
    "BAHIA":               "O Bahia",
    "VITÓRIA":             "O Vitória",
    "VITORIA":             "O Vitória",
    "REMO":                "O Remo",
    "ATHLETICO-PR":        "O Athletico-PR",
    "ATHLETICO PR":        "O Athletico-PR",
    "ATHLETICO":           "O Athletico",
    "RED BULL BRAGANTINO": "O Red Bull Bragantino",
    "RB BRAGANTINO":       "O Red Bull Bragantino",
    "RBB":                 "O Red Bull Bragantino",
    "BRAGANTINO":          "O Bragantino",
    "CHAPECOENSE":         "A Chapecoense",
    "FORTALEZA":           "O Fortaleza",
    "SPORT":               "O Sport",
    "GOIÁS":               "O Goiás",
    "GOIAS":               "O Goiás",
    "CUIABÁ":              "O Cuiabá",
    "CUIABA":              "O Cuiabá",
    "CEARÁ":               "O Ceará",
    "CEARA":               "O Ceará",
    "JUVENTUDE":           "O Juventude",
    "AMERICA-MG":          "O América-MG",
    "AMERICA MG":          "O América-MG",
}

# Perfis que entram na legenda e sua ordem de exibição
_PERFIS_POSITIVOS = {"SG+DE": 0, "SG": 1, "DE": 2}


# ============================================================
# HELPERS DE NOME/ARTIGO
# ============================================================

def format_team_name(team: str) -> str:
    """Grafia correta: 'Atlético-MG', não 'Atlético-Mg'."""
    return _NOMES.get(team.upper().strip(), team.title())


def format_team_article(team: str) -> str:
    """'do Flamengo', 'da Chapecoense' — para 'O goleiro do...'"""
    return _ARTIGOS.get(team.upper().strip(), f"do {format_team_name(team)}")


def format_team_subject(team: str) -> str:
    """'O Flamengo', 'A Chapecoense' — sujeito dentro de frase."""
    return _ARTIGOS_SUJEITO.get(team.upper().strip(), f"O {format_team_name(team)}")


def _safe(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


# ============================================================
# FORMAT_SG — plural correto
# ============================================================

def format_sg(n) -> str:
    """'1 SG' para n=1; '2 SGs' para n>=2 (ou n=0)."""
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        n = 0
    return f"{n} SG" if n == 1 else f"{n} SGs"


# ============================================================
# BOLD FACTORY
# ============================================================

def _make_bold(wrap):
    """Retorna função de negrito para o formato solicitado.

    wrap=None  → identidade (texto puro, sem marcadores)
    wrap='**'  → Telegram Markdown v1  (**texto**)
    wrap='<b>' → HTML                  (<b>texto</b>)
    """
    if wrap == "**":
        return lambda text: f"**{text}**"
    if wrap == "<b>":
        return lambda text: f"<b>{text}</b>"
    return lambda text: text  # texto puro — identidade


# ============================================================
# MOTIVO DE SG (usado no perfil SG isolado)
# ============================================================

def _sg_motivo(sg_t: float, sg_r: float, wrap=None) -> str:
    """Fragmento descritivo do SG — encaixa após 'porque'.
    Nunca termina com ponto."""
    b = _make_bold(wrap)
    try:
        sg_t = float(sg_t)
        sg_r = float(sg_r)
    except (TypeError, ValueError):
        sg_t, sg_r = 0.0, 0.0

    if sg_t >= 2 and sg_r >= 1:
        return (
            f"pegou {b(format_sg(int(sg_t)))} "
            f"e o adversário cedeu {b(format_sg(int(sg_r)))}"
        )
    if sg_t >= 2:
        return f"pegou {b(format_sg(int(sg_t)))} nos últimos 3 jogos"
    if sg_r >= 2:
        return f"o adversário ficou sem marcar em {b(str(int(sg_r)))} jogos"
    total = int(sg_t + sg_r)
    return f"o cruzamento soma {b(str(total))} sinais de SG em 6 possíveis"


# ============================================================
# MONTAGEM DA FRASE — CANÔNICA (única fonte de verdade)
# ============================================================

def _build_entry(time: str, perfil: str, row: dict, mando: str, wrap=None) -> str:
    """Frase completa para um goleiro.

    O formato (plain / Telegram MD / HTML) é controlado por `wrap`.
    Nunca gera barras invertidas nem escapes de MarkdownV2.
    """
    b         = _make_bold(wrap)
    article   = format_team_article(time)   # "do Flamengo"
    subject   = format_team_subject(time)   # "O Flamengo"
    mando_txt = "em casa" if mando == "MANDANTE" else "fora"

    if mando == "MANDANTE":
        sg_t  = _safe(row, "COC_SG")
        sg_r  = _safe(row, "CDF_SG")
        def_t = _safe(row, "COC_DE")
        def_r = _safe(row, "CDF_DE")
    else:
        sg_t  = _safe(row, "COF_SG")
        sg_r  = _safe(row, "CDC_SG")
        def_t = _safe(row, "COF_DE")
        def_r = _safe(row, "CDC_DE")

    sg_t_i  = int(sg_t)
    sg_r_i  = int(sg_r)
    def_t_i = int(def_t)
    def_r_i = int(def_r)

    if perfil == "SG+DE":
        return (
            f"🛡️🧤 {b(f'O goleiro {article}')} tem bom perfil pra {b('SG + DEFESAS')}. "
            f"Nos últimos 3 jogos {mando_txt}, ele pegou {b(format_sg(sg_t_i))} "
            f"e o adversário cedeu {b(format_sg(sg_r_i))}, além disso, "
            f"conquistou {b(f'{def_t_i} defesas')} e o adversário cedeu "
            f"{b(str(def_r_i))} aos goleiros rivais."
        )

    if perfil == "SG":
        motivo = _sg_motivo(sg_t, sg_r, wrap=wrap)
        return (
            f"🛡️ {b(f'O goleiro {article}')} tem perfil mais voltado pra {b('SG')}, "
            f"sem depender tanto de defesas. "
            f"{subject} tem um bom SG porque {motivo}."
        )

    if perfil == "DE":
        return (
            f"🧤 {b(f'O goleiro {article}')} tem bom perfil pra fazer {b('DEFESAS')}. "
            f"Ele conquistou {b(f'{def_t_i} defesas')} nos últimos 3 jogos "
            f"{mando_txt} e o adversário cedeu {b(f'{def_r_i} defesas')} aos goleiros rivais."
        )

    return ""


# ============================================================
# HELPER INTERNO — coleta entradas positivas
# ============================================================

def _collect_entries(goleiros_rows: list) -> list:
    """Filtra e empacota apenas os perfis positivos de uma lista de linhas."""
    entries = []
    for row in goleiros_rows:
        mandante  = str(row.get("MANDANTE", "")).strip()
        visitante = str(row.get("VISITANTE", "")).strip()
        perf_m    = str(row.get("PERFIL_MANDANTE", "-")).strip()
        perf_v    = str(row.get("PERFIL_VISITANTE", "-")).strip()

        if perf_m in ("nan", "None", "", "NaN"):
            perf_m = "-"
        if perf_v in ("nan", "None", "", "NaN"):
            perf_v = "-"

        if perf_m in _PERFIS_POSITIVOS:
            entries.append({
                "order": _PERFIS_POSITIVOS[perf_m],
                "time":  mandante,
                "perfil": perf_m,
                "mando": "MANDANTE",
                "row":   row,
            })
        if perf_v in _PERFIS_POSITIVOS:
            entries.append({
                "order": _PERFIS_POSITIVOS[perf_v],
                "time":  visitante,
                "perfil": perf_v,
                "mando": "VISITANTE",
                "row":   row,
            })
    return entries


# ============================================================
# GERADOR INTERNO — único para todos os formatos
# ============================================================

def _generate(
    goleiros_rows: list,
    rodada: int,
    window_n: int,
    max_entries=None,
    wrap=None,
) -> str:
    b = _make_bold(wrap)

    entries = _collect_entries(goleiros_rows)
    entries.sort(key=lambda e: e["order"])
    if max_entries is not None:
        entries = entries[:max_entries]

    cabecalho = [
        b("ANÁLISE ESTATÍSTICA — GOLEIROS"),
        "",
        f"Destaques positivos — últimos {window_n} jogos por mando.",
    ]

    if not entries:
        return "\n".join(
            cabecalho + ["", "Nenhum goleiro com perfil positivo identificado nesta rodada."]
        )

    lines = cabecalho + [""]
    for e in entries:
        frase = _build_entry(e["time"], e["perfil"], e["row"], e["mando"], wrap=wrap)
        if frase:
            lines.append(frase)
            lines.append("")

    # Remove linhas vazias finais
    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


# ============================================================
# API PÚBLICA
# ============================================================

def generate_goalkeeper_caption(
    goleiros_rows: list,
    rodada: int,
    window_n: int = 3,
    max_entries=None,
) -> str:
    """Legenda em TEXTO PURO — sem marcadores, sem tags HTML."""
    return _generate(goleiros_rows, rodada, window_n, max_entries, wrap=None)


# Alias para compatibilidade
generate_goalkeeper_caption_plain = generate_goalkeeper_caption


def generate_goalkeeper_caption_telegram_md(
    goleiros_rows: list,
    rodada: int,
    window_n: int = 3,
    max_entries=None,
) -> str:
    """Legenda em Telegram Markdown v1 — **negrito** nos termos-chave.

    Ao colar no Telegram Desktop e ENVIAR, os marcadores ** somem
    e o negrito aparece automaticamente na mensagem enviada.

    Nunca usa escapes de MarkdownV2 (sem barras invertidas).
    """
    return _generate(goleiros_rows, rodada, window_n, max_entries, wrap="**")


def generate_goalkeeper_caption_html(
    goleiros_rows: list,
    rodada: int,
    window_n: int = 3,
    max_entries=None,
) -> str:
    """Legenda em HTML com <b>...</b> — para preview no st.markdown."""
    return _generate(goleiros_rows, rodada, window_n, max_entries, wrap="<b>")


# Alias — mantém compatibilidade com app.py
generate_goalkeeper_caption_for_clipboard = generate_goalkeeper_caption_telegram_md
