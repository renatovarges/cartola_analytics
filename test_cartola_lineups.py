import unittest
from unittest.mock import patch
from pathlib import Path

import pandas as pd

from src.cartola_lineups import (build_lineups, build_recent_candidates, inject_lineups,
                                 inject_scout_leaders, player_names, safe_names)
from src.classificacao import load_meias_volantes_classification


class CartolaLineupsTests(unittest.TestCase):
    def test_midfielder_classification_matches_current_roles(self):
        with patch("builtins.print"):
            roles = load_meias_volantes_classification()
        self.assertEqual(roles[("VASCO", "LESCANO")], "MEIA")
        self.assertNotIn(("CORINTHIANS", "KAYKE"), roles)
        self.assertEqual(roles[("GREMIO", "EDENILSON")], "MEIA")
        self.assertEqual(roles[("BOTAFOGO", "EDENILSON")], "VOLANTE")
        self.assertEqual(roles[("INTERNACIONAL", "VILLAGRA")], "VOLANTE")
        reviewed = {
            ("BAHIA", "DAVID MARTINS"): "MEIA",
            ("BOTAFOGO", "DOMINGOS ANDRADE"): "VOLANTE",
            ("BOTAFOGO", "HUGUINHO"): "VOLANTE",
            ("CHAPECOENSE", "BRUNO MATIAS"): "VOLANTE",
            ("CHAPECOENSE", "YAGO FELIPE"): "VOLANTE",
            ("CORITIBA", "VITOR TISSI"): "VOLANTE",
            ("GREMIO", "JEFINHO"): "MEIA",
            ("REMO", "DAVID BRAGA"): "MEIA",
            ("SAO PAULO", "MARCOS ANTONIO"): "MEIA",
            ("VITORIA", "ZE VITOR"): "VOLANTE",
        }
        for key, role in reviewed.items():
            self.assertEqual(roles.get(key), role, key)

    def test_philippe_coutinho_is_classified_for_old_and_new_clubs(self):
        from src import config
        roles = pd.read_csv(Path(config.INPUT_DIR) / "classificacao_meias_volantes.csv")
        entries = roles[roles["JOGADOR"].str.upper().eq("PHILIPPE COUTINHO")]
        self.assertEqual(
            dict(zip(entries["TIME"], entries["CLASSIFICACAO"])),
            {"Vasco": "MEIA", "Santos": "MEIA"},
        )

    def test_nan_name_column_becomes_empty_list(self):
        self.assertEqual(safe_names(float("nan")), [])

    def payload(self):
        return {
            "clubes": {"1": {"slug": "flamengo"}},
            "atletas": [
                {"clube_id": 1, "posicao_id": 1, "status_id": 7, "apelido": "Rossi"},
                {"clube_id": 1, "posicao_id": 1, "status_id": 2, "apelido": "Matheus Cunha"},
                {"clube_id": 1, "posicao_id": 1, "status_id": 5, "apelido": "Goleiro fora"},
                {"clube_id": 1, "posicao_id": 2, "status_id": 7, "apelido": "Varela"},
            ],
        }

    def test_probable_and_doubt_are_kept(self):
        df = pd.DataFrame([
            {"TIME": "FLAMENGO", "NOME": "ROSSI", "POSICAO": 1, "POS_REAL": 1, "DATA": "2026-01-01"},
            {"TIME": "FLAMENGO", "NOME": "MATHEUS CUNHA", "POSICAO": 1, "POS_REAL": 1, "DATA": "2026-01-01"},
            {"TIME": "FLAMENGO", "NOME": "VARELA", "POSICAO": 2, "POS_REAL": 2.2, "DATA": "2026-01-01"},
        ])
        lineups = build_lineups(df, self.payload())
        rows = inject_lineups([{"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO"}], lineups)
        self.assertEqual(rows[0]["JOGADORES_MANDANTE_GOL"], ["Rossi", "Matheus Cunha (Dúvida)"])
        self.assertEqual(rows[0]["JOGADORES_MANDANTE_LD"], ["Varela"])
        self.assertNotIn("Goleiro fora", rows[0]["JOGADORES_MANDANTE_GOL"])

    def test_historical_fallback_marks_lineup_as_unconfirmed(self):
        frame = pd.DataFrame([
            {"TIME": "FLAMENGO", "NOME": "JOAO", "POSICAO": "3", "POS_REAL": 3,
             "DATA": pd.Timestamp("2026-09-01"), "MATCH_ID": "m1"},
        ])
        lineup = build_recent_candidates(frame)
        self.assertEqual(player_names(lineup, "FLAMENGO", "ZAG"),
                         ["JOAO (a confirmar)"])

    def test_all_meaningful_scout_contributors_must_be_probable_or_doubt(self):
        class Engine:
            calls = []
            def get_player_concentration(self, *args, **kwargs):
                self.calls.append(kwargs)
                return pd.DataFrame([
                    {"SCOUT": "CHUTES", "RANK": 1, "NOME": "FORA", "TOTAL": 9,
                     "PARTICIPACAO": 0.35, "JOGOS_COM_SCOUT": 3},
                    {"SCOUT": "CHUTES", "RANK": 2, "NOME": "PEDRO", "TOTAL": 6,
                     "PARTICIPACAO": 0.25, "JOGOS_COM_SCOUT": 2},
                    {"SCOUT": "CHUTES", "RANK": 3, "NOME": "PAULO", "TOTAL": 4,
                     "PARTICIPACAO": 0.22, "JOGOS_COM_SCOUT": 2},
                    {"SCOUT": "CHUTES", "RANK": 4, "NOME": "JOAO", "TOTAL": 3,
                     "PARTICIPACAO": 0.18, "JOGOS_COM_SCOUT": 2},
                ])
        lineups = {"FLAMENGO": {"ATA": [
            {"nome": "Pedro", "status": 7}, {"nome": "Paulo (Dúvida)", "status": 2},
            {"nome": "Joao", "status": 7},
        ]}}
        engine = Engine()
        rows = inject_scout_leaders(
            [{"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO"}],
            lineups, engine, "ATACANTES", 3, mando_mode="TODOS",
        )
        self.assertEqual(rows[0]["DESTAQUES_MANDANTE_CHUTES"],
                         ["Pedro", "Paulo (Dúvida)", "Joao"])
        self.assertNotIn("Fora", rows[0]["DESTAQUES_MANDANTE_CHUTES"])
        self.assertIsNone(engine.calls[0]["mando_filter"])
        self.assertIsNone(engine.calls[0]["max_rank"])


if __name__ == "__main__":
    unittest.main()
