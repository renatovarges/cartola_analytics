import unittest

import pandas as pd

from src.cartola_lineups import build_lineups, inject_lineups, inject_scout_leaders, safe_names


class CartolaLineupsTests(unittest.TestCase):
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

    def test_scout_leader_must_be_probable_or_doubt(self):
        class Engine:
            def get_player_concentration(self, *args, **kwargs):
                return pd.DataFrame([
                    {"SCOUT": "CHUTES", "RANK": 1, "NOME": "FORA", "TOTAL": 9},
                    {"SCOUT": "CHUTES", "RANK": 2, "NOME": "PEDRO", "TOTAL": 6},
                    {"SCOUT": "CHUTES", "RANK": 3, "NOME": "PAULO", "TOTAL": 4},
                ])
        lineups = {"FLAMENGO": {"ATA": [
            {"nome": "Pedro", "status": 7}, {"nome": "Paulo (Dúvida)", "status": 2}
        ]}}
        rows = inject_scout_leaders(
            [{"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO"}],
            lineups, Engine(), "ATACANTES", 3,
        )
        self.assertEqual(rows[0]["DESTAQUES_MANDANTE_CHUTES"], ["Pedro"])
        self.assertNotIn("Fora", rows[0]["DESTAQUES_MANDANTE_CHUTES"])


if __name__ == "__main__":
    unittest.main()
