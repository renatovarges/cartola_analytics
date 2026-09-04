import unittest

from src.engine import CartolaEngine
from src.caption_goleiros import generate_goalkeeper_caption_plain


def base_row(**updates):
    row = {
        "MANDANTE": "A", "VISITANTE": "B", "_WINDOW_N": 3,
        "COC_DE": 0, "CDF_DE": 0, "COF_DE": 0, "CDC_DE": 0,
        "COC_SG": 0, "CDF_SG": 0, "COF_SG": 0, "CDC_SG": 0,
        "COC_CHUTES_AG": 0, "CDF_CHUTES_AG": 0,
        "COF_CHUTES_AG": 0, "CDC_CHUTES_AG": 0,
        "COC_CHUTES_PM": 0, "CDF_CHUTES_PM": 0,
        "COF_CHUTES_PM": 0, "CDC_CHUTES_PM": 0,
        "COC_GOLS": 0, "CDF_GOLS": 0, "COF_GOLS": 0, "CDC_GOLS": 0,
    }
    row.update(updates)
    return row


class GoalkeeperProfileTests(unittest.TestCase):
    def test_paths_are_independent(self):
        row = base_row(COC_DE=12, COF_CHUTES_AG=12, COC_SG=0, CDF_SG=0)
        profile = CartolaEngine.calculate_goalkeeper_profiles(row)[0]
        self.assertEqual(profile["DEFESAS_NIVEL"], "FORTE")
        self.assertEqual(profile["SG_NIVEL"], "-")
        self.assertEqual(profile["PERFIL"], "DEFESAS")

    def test_pressure_alone_does_not_create_save_signal(self):
        row = base_row(COC_DE=5, COF_CHUTES_AG=20)
        profile = CartolaEngine.calculate_goalkeeper_profiles(row)[0]
        self.assertEqual(profile["DEFESAS_NIVEL"], "-")

    def test_sg_does_not_depend_on_save_pressure(self):
        row = base_row(COC_SG=2, CDF_SG=1, COF_GOLS=3, COF_CHUTES_AG=2)
        profile = CartolaEngine.calculate_goalkeeper_profiles(row)[0]
        self.assertEqual(profile["SG_NIVEL"], "FORTE")
        self.assertEqual(profile["DEFESAS_NIVEL"], "-")
        self.assertEqual(profile["PERFIL"], "SG")

    def test_thresholds_scale_to_five_games(self):
        row = base_row(_WINDOW_N=5, COC_DE=19, COF_CHUTES_AG=20)
        profile = CartolaEngine.calculate_goalkeeper_profiles(row)[0]
        self.assertEqual(profile["DEFESAS_NIVEL"], "BOM")

    def test_both_paths_restore_combined_profile(self):
        row = base_row(COC_DE=12, COF_CHUTES_AG=12, COC_SG=2, CDF_SG=1, COF_GOLS=3)
        profile = CartolaEngine.calculate_goalkeeper_profiles(row)[0]
        self.assertEqual(profile["PERFIL"], "AMBOS")

    def test_risk_requires_two_negative_conditions(self):
        only_attack = base_row(COF_GOLS=6, CDC_GOLS=2)
        combined = base_row(COF_GOLS=6, CDC_GOLS=5)
        self.assertEqual(CartolaEngine.calculate_goalkeeper_profiles(only_attack)[0]["PERFIL"], "RISCO")
        self.assertEqual(CartolaEngine.calculate_goalkeeper_profiles(combined)[0]["PERFIL"], "ALTO_RISCO")

    def test_caption_uses_player_and_reason_without_generic_phrase(self):
        row = base_row(COC_DE=12, COC_SG=2)
        row.update({"PERFIL_MANDANTE": "AMBOS", "DEFESAS_NIVEL_MANDANTE": "FORTE",
                    "SG_NIVEL_MANDANTE": "FORTE", "JOGADORES_MANDANTE_GOL": ["Rossi"]})
        text = generate_goalkeeper_caption_plain([row], 23, 3)
        self.assertIn("Rossi combina segurança para SG e volume de defesas", text)
        self.assertNotIn("aparece bem", text)

    def test_caption_lists_doubt_in_parentheses(self):
        row = base_row(COC_DE=12)
        row.update({"PERFIL_MANDANTE": "DEFESAS", "DEFESAS_NIVEL_MANDANTE": "FORTE",
                    "SG_NIVEL_MANDANTE": "-",
                    "JOGADORES_MANDANTE_GOL": ["Rossi", "Matheus Cunha (Dúvida)"]})
        text = generate_goalkeeper_caption_plain([row], 23, 3)
        self.assertIn("Rossi e Matheus Cunha (Dúvida)", text)

    def test_repeated_profiles_use_different_sentence_structures(self):
        rows = []
        for name in ("Warleson", "Ronaldo", "Carlos Miguel"):
            row = base_row(COC_DE=15, COC_SG=1)
            row.update({"PERFIL_MANDANTE": "AMBOS", "DEFESAS_NIVEL_MANDANTE": "FORTE",
                        "SG_NIVEL_MANDANTE": "BOM", "JOGADORES_MANDANTE_GOL": [name]})
            rows.append(row)
        text = generate_goalkeeper_caption_plain(rows, 23, 3)
        self.assertEqual(text.count("pode ser bastante exigido"), 1)
        self.assertEqual(text.count("O melhor caminho"), 1)
        self.assertEqual(text.count("boas oportunidades"), 1)

    def test_balanced_profiles_beat_isolated_strong_signals(self):
        specs = [
            ("Gabriel Brazão", "FORTE", "BOM", "AMBOS", 10, 2),
            # Na rodada real, o perfil final é AMBOS mesmo quando os dois
            # componentes individuais ainda estão na faixa SINAL.
            ("Carlos Miguel", "SINAL", "SINAL", "AMBOS", 10, 1),
            ("Everson", "SINAL", "SINAL", "AMBOS", 10, 1),
            ("Mycael", "-", "FORTE", "DEFESAS", 12, 0),
            ("Rossi", "-", "FORTE", "DEFESAS", 12, 0),
            ("Ronaldo", "FORTE", "-", "SG", 15, 2),
            ("Tiago Volpi", "FORTE", "-", "SG", 15, 2),
        ]
        rows = []
        for name, sg, de, profile, saves, clean_sheets in specs:
            candidate = base_row(COC_DE=saves, COC_SG=clean_sheets)
            candidate.update({
                "PERFIL_MANDANTE": profile,
                "PERFIL_VISITANTE": "-",
                "SG_NIVEL_MANDANTE": sg,
                "DEFESAS_NIVEL_MANDANTE": de,
                "JOGADORES_MANDANTE_GOL": [name],
            })
            rows.append(candidate)

        text = generate_goalkeeper_caption_plain(rows, 26, 3)
        for selected in ("Gabriel Brazão", "Carlos Miguel", "Everson", "Mycael", "Rossi"):
            self.assertIn(selected, text)
        self.assertNotIn("Ronaldo", text)
        self.assertNotIn("Tiago Volpi", text)
        self.assertIn("Seleção revisada", text)


if __name__ == "__main__":
    unittest.main()
