"""Consulta e cruza os prováveis do Cartola com as posições da planilha."""

from __future__ import annotations

import json
import os
import time
import unicodedata
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

import pandas as pd

from . import config


API_URL = "https://api.cartolafc.globo.com/atletas/mercado"
CACHE_PATH = Path(config.INPUT_DIR) / "cartola_provaveis_cache.json"
CACHE_SECONDS = 15 * 60


def _key(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).upper().strip()


def _canonical_team(value) -> str:
    name = _key(value)
    api_aliases = {
        "RED-BULL-BRAGANTINO": "RED BULL BRAGANTINO",
        "ATLETICO-MG": "ATLETICO-MG",
        "ATHLETICO-PR": "ATHLETICO-PR",
        "SAO-PAULO": "SAO PAULO",
    }
    name = api_aliases.get(name, name)
    aliases = {_key(k): _key(v) for k, v in config.TEAM_ALIASES.items()}
    return aliases.get(name, name)


def fetch_market(timeout=8, force=False) -> dict:
    """Busca o mercado e usa cache recente; em falha, aceita o último cache."""
    if not force and CACHE_PATH.exists() and time.time() - CACHE_PATH.stat().st_mtime < CACHE_SECONDS:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    try:
        request = Request(API_URL, headers={"User-Agent": "CartolaAnalytics/2026"})
        # Não herda proxy inválido do ambiente local; a URL é pública e HTTPS.
        with build_opener(ProxyHandler({})).open(request, timeout=timeout) as response:
            payload = json.load(response)
        CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload
    except Exception:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return {}


def _local_roles(df_players: pd.DataFrame) -> dict[tuple[str, str], str]:
    """Mapeia nome+time para LE/LD e MEI/VOL usando a base local."""
    roles = {}
    if df_players is None or df_players.empty:
        return roles
    latest = df_players.sort_values("DATA").drop_duplicates(["TIME", "NOME"], keep="last")
    classification = {}
    path = Path(config.INPUT_DIR) / "classificacao_meias_volantes.csv"
    if path.exists():
        c = pd.read_csv(path)
        classification = {(_canonical_team(r.TIME), _key(r.JOGADOR)): _key(r.CLASSIFICACAO) for r in c.itertuples()}
    for row in latest.itertuples():
        team, name = _canonical_team(row.TIME), _key(row.NOME)
        pos = int(float(row.POSICAO)) if pd.notna(row.POSICAO) else 0
        real = float(row.POS_REAL) if hasattr(row, "POS_REAL") and pd.notna(row.POS_REAL) else 0
        role = {1: "GOL", 3: "ZAG", 5: "ATA"}.get(pos)
        if pos == 2:
            role = "LE" if round(real, 1) == 2.6 else "LD" if round(real, 1) == 2.2 else "LAT"
        elif pos == 4:
            role = "VOL" if classification.get((team, name)) == "VOLANTE" else "MEI"
        if role:
            roles[(team, name)] = role
    return roles


def build_lineups(df_players: pd.DataFrame, payload=None) -> dict:
    """Retorna time -> função -> nomes, incluindo dúvidas identificadas."""
    payload = payload if payload is not None else fetch_market()
    if not payload or "atletas" not in payload:
        return {}
    clubs = {int(k): _canonical_team(v.get("slug") or v.get("apelido") or v.get("nome"))
             for k, v in payload.get("clubes", {}).items()}
    local = _local_roles(df_players)
    api_roles = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA"}
    result = {}
    for athlete in payload["atletas"]:
        status = int(athlete.get("status_id") or 0)
        if status not in {2, 7}:
            continue
        team = clubs.get(int(athlete.get("clube_id") or 0), "")
        name_key = _key(athlete.get("apelido"))
        role = local.get((team, name_key), api_roles.get(int(athlete.get("posicao_id") or 0)))
        label = str(athlete.get("apelido") or athlete.get("nome") or "").strip()
        if status == 2:
            label += " (Dúvida)"
        result.setdefault(team, {}).setdefault(role, []).append({"nome": label, "status": status})
    return result


def player_names(lineups: dict, team: str, role: str) -> list[str]:
    entries = lineups.get(_canonical_team(team), {}).get(role, [])
    probable = [e["nome"] for e in entries if e["status"] == 7]
    doubts = [e["nome"] for e in entries if e["status"] == 2]
    return probable + doubts


def inject_lineups(rows: list[dict], lineups: dict) -> list[dict]:
    """Acrescenta nomes às linhas sem alterar métricas estatísticas."""
    for row in rows:
        for side in ("MANDANTE", "VISITANTE"):
            team = row.get(side, "")
            for role in ("GOL", "LE", "LD", "LAT", "ZAG", "MEI", "VOL", "ATA"):
                row[f"JOGADORES_{side}_{role}"] = player_names(lineups, team, role)
    return rows


def _lineup_lookup(lineups: dict, team: str, roles: tuple[str, ...]) -> dict[str, str]:
    """Nome normalizado -> rótulo público, restrito a provável ou dúvida."""
    found = {}
    club = lineups.get(_canonical_team(team), {})
    for role in roles:
        for entry in club.get(role, []):
            label = entry["nome"]
            clean = label.replace(" (Dúvida)", "")
            found[_key(clean)] = label
    return found


def inject_scout_leaders(rows: list[dict], lineups: dict, engine, position: str,
                         window_n: int = 3, date_cutoff=None) -> list[dict]:
    """Vincula cada scout somente a atletas prováveis/dúvidas que o produziram.

    A tabela continua coletiva. Esses campos existem apenas para impedir que a
    legenda atribua um destaque a todo provável da posição ou a um atleta fora.
    """
    pos = str(position).upper()
    role_map = {
        "MEIAS": ("MEI",), "VOLANTES": ("VOL",), "ATACANTES": ("ATA",),
        "ZAGUEIROS": ("ZAG",), "LATERAIS": ("LE", "LD", "LAT"),
    }
    roles = role_map.get(pos)
    if not roles:
        return rows
    for row in rows:
        for side, mando in (("MANDANTE", "CASA"), ("VISITANTE", "FORA")):
            team = str(row.get(side, "")).strip()
            eligible = _lineup_lookup(lineups, team, roles)
            if not team or not eligible:
                continue
            concentration = engine.get_player_concentration(
                team, pos, window_n=window_n, mando_filter=mando,
                date_cutoff=date_cutoff,
            )
            if concentration is None or concentration.empty:
                continue
            for scout, group in concentration.groupby("SCOUT", sort=False):
                matches = []
                for item in group.sort_values(["RANK", "NOME"]).itertuples():
                    label = eligible.get(_key(item.NOME))
                    if label:
                        matches.append((label, float(item.TOTAL)))
                if not matches:
                    continue
                best = matches[0][1]
                # Empates reais são mantidos; não transformamos toda a posição em opção.
                names = [label for label, value in matches if value == best]
                row[f"DESTAQUES_{side}_{scout}"] = names
                if pos == "LATERAIS":
                    for lateral_role in ("LE", "LD"):
                        lateral_eligible = _lineup_lookup(lineups, team, (lateral_role,))
                        lateral_matches = [
                            (lateral_eligible[_key(item.NOME)], float(item.TOTAL))
                            for item in group.sort_values(["RANK", "NOME"]).itertuples()
                            if _key(item.NOME) in lateral_eligible
                        ]
                        if lateral_matches:
                            lateral_best = lateral_matches[0][1]
                            row[f"DESTAQUES_{side}_{lateral_role}_{scout}"] = [
                                label for label, value in lateral_matches if value == lateral_best
                            ]
    return rows
