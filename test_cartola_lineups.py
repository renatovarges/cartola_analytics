import unittest

import pandas as pd

from src.cartola_lineups import build_lineups, inject_lineups


class CartolaLineupsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
