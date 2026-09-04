"""Legendas simples para os destaques coletivos de volantes."""

from .caption_meias import _fmt_team, _make_bold, _safe, format_pg, format_pontos


def _generate(rows, rodada, window_n=3, wrap=None):
    b = _make_bold(wrap)
    candidates = []
    for row in rows:
        for team_key, own, conceded, mando in (
            ("MANDANTE", "COC", "CDF", "em casa"),
            ("VISITANTE", "COF", "CDC", "fora"),
        ):
            team = str(row.get(team_key, "")).strip()
            if not team:
                continue
            de = _safe(row, f"{own}_DE")
            de_c = _safe(row, f"{conceded}_DE")
            pg = _safe(row, f"{own}_PG")
            pg_c = _safe(row, f"{conceded}_PG")
            bas = _safe(row, f"{own}_BASICA")
            bas_c = _safe(row, f"{conceded}_BASICA")
            factor = max(window_n, 1) / 3
            scouts = set()
            if de >= 17 * factor or (de >= 14 * factor and de_c >= 14 * factor): scouts.add("de")
            if bas >= 4.8 or (bas >= 4.0 and bas_c >= 4.0): scouts.add("bas")
            if pg >= 4 * factor or (pg >= 3 * factor and pg_c >= 3 * factor): scouts.add("pg")
            if scouts:
                candidates.append({"team": team, "mando": mando, "de": de, "bas": bas,
                    "pg": pg, "scouts": scouts, "leaders": {
                        "de": row.get(f"DESTAQUES_{team_key}_DE", []) or [],
                        "bas": row.get(f"DESTAQUES_{team_key}_BASICA", []) or [],
                        "pg": row.get(f"DESTAQUES_{team_key}_PG", []) or []}})

    candidates.sort(key=lambda e: ("de" in e["scouts"], "bas" in e["scouts"],
                                    len(e["scouts"]), e["de"], e["bas"]), reverse=True)
    lines = [b("ANÁLISE ESTATÍSTICA — VOLANTES"), "", f"Destaques dos últimos {window_n} jogos por mando."]
    if candidates:
        lines += ["", b("🧱 DESTAQUES ENTRE OS VOLANTES"), ""]
    for e in candidates[:5]:
        subject = b(f"Os volantes {_fmt_team(e['team'])}")
        facts = []
        if "de" in e["scouts"]: facts.append(f"{int(e['de'])} desarmes")
        if "bas" in e["scouts"]: facts.append(f"média básica de {format_pontos(e['bas'])} pontos")
        if "pg" in e["scouts"]: facts.append(format_pg(e["pg"]).lower())
        links = []
        labels = {"de": "desarmes", "bas": "pontuação básica", "pg": "G + A"}
        for key in ("de", "bas", "pg"):
            if key in e["scouts"] and e["leaders"][key]: links.append(f"{labels[key]} — {b(' / '.join(e['leaders'][key]))}")
        suffix = f" Destaques individuais: {'; '.join(links)}." if links else ""
        lines.append(f"{subject}: {'; '.join(facts)} nos últimos {window_n} jogos {e['mando']}.{suffix}")
    if not candidates:
        lines += ["", "Nenhum grupo de volantes passou nos filtros desta rodada."]
    return "\n".join(lines)


def generate_volantes_caption_plain(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n)


def generate_volantes_caption_telegram_md(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n, "**")


def generate_volantes_caption_html(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n, "<b>")
