"""Legendas simples para os destaques coletivos de volantes."""

from .caption_meias import _fmt_team, _make_bold, _safe, format_pg, format_pontos


def _generate(rows, rodada, window_n=3, wrap=None):
    b = _make_bold(wrap)
    desarmes, basicas, ofensivas = [], [], []
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
            article = _fmt_team(team)
            players = row.get(f"JOGADORES_{team_key}_VOL", []) or []
            prefix = ("Opções: " + " / ".join(players) + ". ") if players else ""
            factor = max(window_n, 1) / 3
            if de >= 17 * factor or (de >= 14 * factor and de_c >= 14 * factor):
                text = prefix + f"Os volantes {article} fizeram {int(de)} desarmes nos últimos {window_n} jogos {mando}."
                if de_c >= 14 * factor:
                    text += f" O adversário também cedeu {int(de_c)} desarmes a volantes."
                desarmes.append(text)
            if bas >= 4.8 or (bas >= 4.0 and bas_c >= 4.0):
                basicas.append(
                    prefix + f"Os volantes {article} tiveram média básica de {format_pontos(bas)} pontos nos últimos {window_n} jogos {mando}."
                )
            if pg >= 4 * factor or (pg >= 3 * factor and pg_c >= 3 * factor):
                ofensivas.append(
                    prefix + f"Os volantes {article} somaram {format_pg(pg).lower()} nos últimos {window_n} jogos {mando}."
                )

    desarmes.sort(key=lambda text: int(text.split(" fizeram ", 1)[1].split(" ", 1)[0]), reverse=True)
    basicas.sort(key=lambda text: float(text.split(" de ", 1)[1].split(" ", 1)[0].replace(",", ".")), reverse=True)
    ofensivas.sort()
    lines = [b("ANÁLISE ESTATÍSTICA — VOLANTES"), "", f"Destaques dos últimos {window_n} jogos por mando."]
    for title, entries in (("VOLANTES PARA DESARMES", desarmes[:2]),
                           ("VOLANTES PARA PONTUAÇÃO BÁSICA", basicas[:2]),
                           ("PARTICIPAÇÃO OFENSIVA — COMPLEMENTO", ofensivas[:2])):
        if entries:
            lines += ["", b(title), ""] + [b(e) if False else e for e in entries]
    if len(lines) == 3:
        lines += ["", "Nenhum grupo de volantes passou nos filtros desta rodada."]
    return "\n".join(lines)


def generate_volantes_caption_plain(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n)


def generate_volantes_caption_telegram_md(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n, "**")


def generate_volantes_caption_html(rows, rodada, window_n=3):
    return _generate(rows, rodada, window_n, "<b>")
