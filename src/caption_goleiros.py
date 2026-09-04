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
_PERFIS_POSITIVOS = {"AMBOS": 0, "SG": 1, "DEFESAS": 2}


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

def _build_entry(time: str, perfil: str, row: dict, mando: str, wrap=None, variant=0) -> str:
    """Frase completa para um goleiro.

    O formato (plain / Telegram MD / HTML) é controlado por `wrap`.
    Nunca gera barras invertidas nem escapes de MarkdownV2.
    """
    b         = _make_bold(wrap)
    article   = format_team_article(time)   # "do Flamengo"
    subject   = format_team_subject(time)   # "O Flamengo"
    mando_txt = "em casa" if mando == "MANDANTE" else "fora"
    jogadores = row.get(f"JOGADORES_{mando}_GOL", []) or []
    if jogadores:
        subject_gol = " e ".join(jogadores)
    else:
        subject_gol = f"O goleiro {article}"
    sg_level = str(row.get(f"SG_NIVEL_{mando}", "-"))
    def_level = str(row.get(f"DEFESAS_NIVEL_{mando}", "-"))

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

    if perfil == "AMBOS":
        if sg_level == "FORTE" and def_level != "FORTE":
            templates = [
                f"🛡️🧤 {b(subject_gol)} tem {b('o SG como principal atrativo')}, com espaço também para defesas. O time pegou {b(format_sg(sg_t_i))} e o goleiro fez {b(f'{def_t_i} defesas')} nos últimos jogos {mando_txt}.",
                f"🛡️🧤 O confronto de {b(subject_gol)} favorece mais o {b('SG')}, mas ainda pode render defesas. Foram {b(format_sg(sg_t_i))} e {b(f'{def_t_i} defesas')} no recorte {mando_txt}.",
                f"🛡️🧤 {b(subject_gol)} chega com {b('cenário forte para SG')}. As {b(f'{def_t_i} defesas')} recentes acrescentam uma segunda possibilidade de pontuação.",
            ]
        elif def_level == "FORTE" and sg_level != "FORTE":
            templates = [
                f"🛡️🧤 {b(subject_gol)} pode ser bastante exigido: fez {b(f'{def_t_i} defesas')} nos últimos jogos {mando_txt}. O time também conseguiu {b(format_sg(sg_t_i))}.",
                f"🛡️🧤 O melhor caminho para {b(subject_gol)} está nas {b('defesas')}. Foram {b(f'{def_t_i}')} no recorte, além de {b(format_sg(sg_t_i))}.",
                f"🛡️🧤 {b(subject_gol)} encontra boas oportunidades para {b('pontuar com defesas')}. Também passou sem sofrer gols em {b(format_sg(sg_t_i))} no período.",
            ]
        else:
            templates = [
                f"🛡️🧤 {b(subject_gol)} combina {b('segurança para SG e volume de defesas')}: registrou {b(f'{def_t_i} defesas')} e {b(format_sg(sg_t_i))} nos últimos jogos {mando_txt}.",
                f"🛡️🧤 O cenário de {b(subject_gol)} é completo. Há bons sinais tanto para {b('SG')} quanto para defesas, com {b(f'{def_t_i} defesas')} e {b(format_sg(sg_t_i))} no recorte.",
                f"🛡️🧤 {b(subject_gol)} oferece duas rotas de pontuação: {b('SG e defesas')}. No período, somou {b(f'{def_t_i} defesas')} e conseguiu {b(format_sg(sg_t_i))}.",
            ]
        return templates[variant % len(templates)]

    if perfil == "SG":
        templates = [
            f"🛡️ {b(subject_gol)} tem {b('boas condições de sair com SG')}. O time pegou {b(format_sg(sg_t_i))} nos últimos jogos {mando_txt}.",
            f"🛡️ O principal atrativo de {b(subject_gol)} é o {b('potencial de SG')}: foram {b(format_sg(sg_t_i))} no recorte {mando_txt}.",
            f"🛡️ {b(subject_gol)} encontra um {b('confronto interessante para SG')}. O time passou {b(format_sg(sg_t_i))} sem sofrer gols no período.",
        ]
        return templates[variant % len(templates)]

    if perfil == "DEFESAS":
        templates = [
            f"🧤 {b(subject_gol)} tem {b('bom potencial para acumular defesas')}. Fez {b(f'{def_t_i} defesas')} nos últimos jogos {mando_txt}.",
            f"🧤 O confronto pode exigir bastante de {b(subject_gol)}. As {b(f'{def_t_i} defesas')} recentes reforçam essa possibilidade.",
            f"🧤 {b(subject_gol)} surge como opção para quem busca {b('pontuação por defesas')}, após {b(f'{def_t_i}')} no recorte {mando_txt}.",
        ]
        return templates[variant % len(templates)]

    return ""


# ============================================================
# HELPER INTERNO — coleta entradas positivas
# ============================================================

_LEVEL_VALUE = {"-": 0, "SINAL": 1, "BOM": 2, "FORTE": 3}


def _profile_priority(sg_level: str, def_level: str) -> int:
    """Hierarquia da legenda baseada no cenário completo do goleiro.

    Equilíbrio em dois caminhos supera força isolada. Entre os perfis de um
    caminho só, defesas vêm antes de SG porque ainda oferecem pontuação mesmo
    quando o time sofre gol.
    """
    sg = _LEVEL_VALUE.get(str(sg_level), 0)
    de = _LEVEL_VALUE.get(str(def_level), 0)
    if sg == 3 and de == 3:
        return 600
    if min(sg, de) >= 2 and max(sg, de) == 3:
        return 550
    if sg >= 2 and de >= 2:
        return 500
    if de == 3:
        return 400
    if sg == 3:
        return 300
    return 0

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

        priority_m = _profile_priority(row.get("SG_NIVEL_MANDANTE", "-"), row.get("DEFESAS_NIVEL_MANDANTE", "-"))
        priority_v = _profile_priority(row.get("SG_NIVEL_VISITANTE", "-"), row.get("DEFESAS_NIVEL_VISITANTE", "-"))

        if perf_m in _PERFIS_POSITIVOS and priority_m:
            entries.append({
                "order": _PERFIS_POSITIVOS[perf_m],
                "priority": priority_m,
                "volume": _safe(row, "COC_DE") + 3 * _safe(row, "COC_SG"),
                "time":  mandante,
                "perfil": perf_m,
                "mando": "MANDANTE",
                "row":   row,
            })
        if perf_v in _PERFIS_POSITIVOS and priority_v:
            entries.append({
                "order": _PERFIS_POSITIVOS[perf_v],
                "priority": priority_v,
                "volume": _safe(row, "COF_DE") + 3 * _safe(row, "COF_SG"),
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
    entries.sort(key=lambda e: (e["priority"], e["volume"], -e["order"]), reverse=True)
    if max_entries is None:
        max_entries = 5
    if max_entries is not None:
        entries = entries[:max_entries]

    cabecalho = [
        b("ANÁLISE ESTATÍSTICA — GOLEIROS"),
        "",
        f"Seleção revisada — últimos {window_n} jogos por mando.",
    ]

    if not entries:
        return "\n".join(
            cabecalho + ["", "Nenhum goleiro com perfil positivo identificado nesta rodada."]
        )

    lines = cabecalho + [""]
    for index, e in enumerate(entries):
        frase = _build_entry(e["time"], e["perfil"], e["row"], e["mando"], wrap=wrap, variant=index)
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
