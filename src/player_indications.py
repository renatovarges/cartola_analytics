"""Indicações por atleta, independentes do corte coletivo da legenda.

As réguas são percentis de janelas anteriores à data de análise. Frequência
é requisito explícito apenas onde a validação de cobertura o sustentou.
"""

from __future__ import annotations

from collections import defaultdict
import math

import pandas as pd

from .cartola_lineups import _canonical_team, _key, _local_roles, _lineup_lookup


POSITION_ROLES = {
    "ATACANTES": ("ATA",), "MEIAS": ("MEI",), "VOLANTES": ("VOL",),
    "LATERAIS": ("LE", "LD"), "ZAGUEIROS": ("ZAG",),
}
METRICS = {
    "ATA": ("CHUTES", "PG"), "MEI": ("CHUTES", "PG"),
    "VOL": ("DE", "PG"), "LE": ("DE",),
    "LD": ("DE",), "ZAG": ("DE",),
}
HIT_FLOOR = {"DE": 2, "CHUTES": 1, "PG": 1}
MIN_TOTAL = {"DE": 4, "CHUTES": 2, "PG": 2}
SELECTION_RULES = {
    ("ATA", "CHUTES"): (.75, 3),
    ("MEI", "CHUTES"): (.80, 2),
    ("VOL", "DE"): (.80, 2),
    ("LE", "DE"): (.80, 2),
    ("LD", "DE"): (.85, 2),
    ("ZAG", "DE"): (.85, 2),
}
DEFAULT_RULE = (.90, 2)
METRIC_WORD = {"DE": "desarmes", "CHUTES": "finalizações", "PG": "participações em gol"}
OCCURRENCE_WORD = {"DE": "2+ desarmes", "CHUTES": "finalização",
                   "PG": "participação em gol"}
ROLE_WORD = {"ATA": "atacantes", "MEI": "meias", "VOL": "volantes",
             "LE": "laterais esquerdos", "LD": "laterais direitos", "ZAG": "zagueiros"}
VOLUME_METRICS = {"DE", "CHUTES"}


def _number(value) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}".replace(".", ",")


def recurrence_gate(values, metric: str, minimum_hits: int) -> tuple[int, int, int, bool]:
    """Exige frequência proporcional e scout recente; G+A mantém régua própria."""
    flags = [float(value) >= HIT_FLOOR[metric] for value in values]
    hits = sum(flags)
    volume = metric in VOLUME_METRICS
    required = max(minimum_hits, math.ceil(.60 * len(flags))) if volume else minimum_hits
    recent_hits = sum(flags[-2:] if volume else flags[-3:])
    return hits, required, recent_hits, hits >= required and recent_hits >= 1


def _source(engine, cutoff) -> pd.DataFrame:
    raw = engine.df_pj
    if cutoff is not None:
        raw = raw[raw.DATA.lt(pd.to_datetime(cutoff))]
    raw = raw[raw.DATA.notna()].copy()
    if raw.empty:
        return raw
    raw["TEAM_KEY"] = raw.TIME.map(_canonical_team)
    raw["ADVERSARIO_KEY"] = raw.ADVERSARIO.map(_canonical_team)
    role_lookup = _local_roles(raw)
    raw["ROLE"] = [role_lookup.get((_canonical_team(team), _key(name)))
                   for team, name in zip(raw.TIME, raw.NOME)]
    for metric, columns in {"DE": ("DS",), "CHUTES": ("FF", "FD", "FT"),
                            "PG": ("G", "A")}.items():
        raw[metric] = sum((pd.to_numeric(raw.get(col, pd.Series(0, index=raw.index)), errors="coerce")
                           .fillna(0).clip(lower=0) for col in columns))
    return raw.sort_values(["DATA", "MATCH_ID"])


def _quantiles(raw: pd.DataFrame) -> dict:
    """Compara médias por aparição, evitando punir quem fez 3 em vez de 5 jogos."""
    reference = {}
    for role, metrics in METRICS.items():
        subset = raw[raw.ROLE.eq(role)]
        for metric in metrics:
            values = []
            for _, games in subset.groupby(["TIME", "NOME"]):
                series = games.sort_values("DATA")[metric]
                values.extend(series.rolling(5, min_periods=3).mean().dropna().tolist())
            if len(values) >= 25:
                quantile = pd.Series(values).quantile([.75, .80, .85, .90])
                reference[(role, metric)] = {p: float(quantile.loc[p])
                                             for p in (.75, .80, .85, .90)}
    conceded = {}
    for role, metrics in METRICS.items():
        subset = raw[raw.ROLE.eq(role)]
        for metric in metrics:
            totals = subset.groupby(["ADVERSARIO_KEY", "MATCH_ID"])[metric].sum()
            if len(totals) >= 25:
                conceded[(role, metric)] = max(
                    HIT_FLOOR[metric], float(totals.quantile(.75)))
    return {"own": reference, "conceded": conceded}


def _opponent_games(raw: pd.DataFrame, opponent: str, role: str,
                    metric: str, n: int = 5) -> list[float]:
    games = (raw[raw.TEAM_KEY.eq(_canonical_team(opponent))][["MATCH_ID", "DATA"]]
             .drop_duplicates("MATCH_ID").sort_values("DATA").tail(n))
    if len(games) < 3:
        return []
    yielded = (raw[raw.ADVERSARIO_KEY.eq(_canonical_team(opponent)) & raw.ROLE.eq(role)]
               .groupby("MATCH_ID")[metric].sum())
    return [float(yielded.get(match_id, 0)) for match_id in games.MATCH_ID]


def _keeper_evidence(raw: pd.DataFrame, lineups: dict, opponent: str):
    eligible = _lineup_lookup(lineups, opponent, ("GOL",))
    if not eligible or "GS" not in raw:
        return None
    keepers = raw[(raw.TEAM_KEY.eq(_canonical_team(opponent))) &
                  (raw.POSICAO.isin(["1", "1.0"]))]
    candidates = []
    recent_matches = _team_recency(raw, opponent)
    for name, games in keepers.groupby("NOME"):
        label = eligible.get(_key(name))
        if not label:
            continue
        recent = games.sort_values("DATA").tail(5)
        if len(recent) >= 4 and recent.MATCH_ID.iloc[-1] in recent_matches:
            gs = pd.to_numeric(recent.GS, errors="coerce").fillna(0)
            hits = int(gs.ge(2).sum())
            if hits >= 3:
                candidates.append((not label.endswith(" (Dúvida)"), recent.DATA.iloc[-1],
                                   {"nome": label, "hits": hits, "jogos": len(recent)}))
    return max(candidates, key=lambda item: item[:2])[2] if candidates else None


def _team_recency(raw: pd.DataFrame, team: str) -> set:
    return set(raw[raw.TEAM_KEY.eq(_canonical_team(team))].sort_values("DATA")
               .drop_duplicates("MATCH_ID").tail(4).MATCH_ID)


def analyse_matchups(engine, lineups: dict, rows: list[dict], position: str,
                     date_cutoff=None) -> tuple[list[dict], list[dict]]:
    """Retorna indicações e trilha de elegibilidade, com corte temporal estrito."""
    pos = str(position).upper()
    roles = POSITION_ROLES.get(pos, ())
    if not roles:
        return [], []
    raw = _source(engine, date_cutoff)
    if raw.empty:
        return [], []
    thresholds = _quantiles(raw)
    indications, audit = [], []
    for row in rows:
        for side, other in (("MANDANTE", "VISITANTE"), ("VISITANTE", "MANDANTE")):
            team, opponent = str(row.get(side, "")), str(row.get(other, ""))
            eligible = _lineup_lookup(lineups, team, roles)
            if not eligible:
                continue
            recent_team_matches = _team_recency(raw, team)
            own = raw[raw.TEAM_KEY.eq(_canonical_team(team)) & raw.ROLE.isin(roles)]
            keeper = _keeper_evidence(raw, lineups, opponent)
            for name, games in own.groupby("NOME"):
                label = eligible.get(_key(name))
                if not label:
                    continue
                games = games.sort_values("DATA").tail(5)
                role = str(games.ROLE.iloc[-1])
                fresh = games.MATCH_ID.iloc[-1] in recent_team_matches
                for metric in METRICS.get(role, ()):
                    values = games[metric]
                    total = float(values.sum())
                    ref = thresholds["own"].get((role, metric))
                    percentile, minimum_hits = SELECTION_RULES.get(
                        (role, metric), DEFAULT_RULE)
                    hits, required_hits, recent_hits, sustained = recurrence_gate(
                        values, metric, minimum_hits)
                    own_rate = total / len(games)
                    strong = bool(ref and own_rate >= ref[percentile] and
                                  total >= MIN_TOTAL[metric] and hits >= minimum_hits)
                    moderate = bool(ref and own_rate >= ref[.75] and
                                    total >= MIN_TOTAL[metric] and hits >= 2)
                    conceded = _opponent_games(raw, opponent, role, metric)
                    cut = thresholds["conceded"].get((role, metric))
                    conceded_hits = (sum(value >= cut for value in conceded)
                                      if cut is not None else 0)
                    opponent_pattern = (len(conceded) >= 4 and
                                        conceded_hits >= max(3, math.ceil(.75 * len(conceded))))
                    crossed = moderate and opponent_pattern
                    selected = len(games) >= 3 and fresh and strong and sustained
                    item = {
                        "time": team, "adversario": opponent, "lado": side,
                        "jogador": label, "posicao": role, "scout": metric,
                        "total": total, "jogos": len(games), "ocorrencias": hits,
                        "recorrente": sustained,
                        "percentil_75": ref[.75] if ref else None,
                        "percentil_80": ref[.80] if ref else None,
                        "percentil_85": ref[.85] if ref else None,
                        "percentil_90": ref[.90] if ref else None,
                        "percentil_exigido": percentile,
                        "ocorrencias_exigidas": required_hits,
                        "ocorrencias_recentes": recent_hits,
                        "janela_recente": 2 if metric in VOLUME_METRICS else 3,
                        "cedidos": sum(conceded), "jogos_adversario": len(conceded),
                        "ocorrencias_cedidas": conceded_hits, "corte_cedido": cut,
                        "forte": strong, "recorrencia_sustentada": sustained,
                        "cruzamento": crossed, "selecionado": selected,
                        "motivo": ("selecionado" if selected else "amostra_curta" if len(games) < 3
                                   else "sem_jogo_recente" if not fresh
                                   else "recorrencia_fraca" if strong and not sustained
                                   else "abaixo_dos_cortes"),
                    }
                    if selected and metric == "PG" and keeper:
                        item["goleiro_adversario"] = keeper
                    audit.append(item)
                    if selected:
                        indications.append(item)
    return indications, audit


def inject_player_indications(rows: list[dict], lineups: dict, engine,
                              position: str, date_cutoff=None) -> list[dict]:
    indications, audit = analyse_matchups(engine, lineups, rows, position, date_cutoff)
    by_match = defaultdict(list)
    for item in indications:
        by_match[(item["time"], item["adversario"])].append(item)
    for row in rows:
        row[f"INDICACOES_{position.upper()}"] = (
            by_match.get((row.get("MANDANTE"), row.get("VISITANTE")), []) +
            by_match.get((row.get("VISITANTE"), row.get("MANDANTE")), []))
        row[f"AUDITORIA_{position.upper()}"] = [
            item for item in audit if (item["time"], item["adversario"]) in {
                (row.get("MANDANTE"), row.get("VISITANTE")),
                (row.get("VISITANTE"), row.get("MANDANTE"))}]
    return rows


def append_individual_section(lines: list[str], rows: list[dict], position: str,
                              wrap=None) -> None:
    """Adiciona frases auditáveis mesmo sem destaque coletivo da posição."""
    grouped = defaultdict(lambda: defaultdict(list))
    venue = {}
    for row in rows:
        home, away = row.get("MANDANTE"), row.get("VISITANTE")
        venue[(home, away)] = "em casa"
        venue[(away, home)] = "fora"
        for item in row.get(f"INDICACOES_{position.upper()}", []):
            grouped[(item["time"], item["adversario"])][item["jogador"]].append(item)
    if not grouped:
        return
    bold = (lambda value: f"{wrap}{value}{'**' if wrap == '**' else '</b>'}"
            if wrap else value)
    lines.extend(["", bold("PADRÕES INDIVIDUAIS E CRUZAMENTOS — ATÉ 5 JOGOS GERAIS"), ""])
    for (team, opponent), players in grouped.items():
        local = venue.get((team, opponent))
        lines.append(bold(f"{team} ({local}) contra {opponent}" if local else f"{team} contra {opponent}"))
        for name, items in players.items():
            clauses = []
            for item in items:
                metric = item["scout"]
                fact = (f"{_number(item['total'])} {METRIC_WORD[metric]} em "
                        f"{item['jogos']} jogos")
                fact += (f" ({item['ocorrencias']}/{item['jogos']} jogos com "
                         f"{OCCURRENCE_WORD[metric]})")
                if item["cruzamento"]:
                    fact += (f"; adversário cedeu {METRIC_WORD[metric]} a "
                             f"{ROLE_WORD[item['posicao']]} em "
                             f"{item['ocorrencias_cedidas']}/{item['jogos_adversario']} jogos")
                keeper = item.get("goleiro_adversario")
                if keeper:
                    fact += (f"; {keeper['nome']} sofreu 2+ gols em "
                             f"{keeper['hits']}/{keeper['jogos']} jogos")
                clauses.append(fact)
            lines.append(f"{bold(name)}: {'; '.join(clauses)}.")
