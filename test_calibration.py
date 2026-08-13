import unittest

from src.calibration import classify, classify_cell, get_thresholds


class CalibrationBoundaryTests(unittest.TestCase):
    def test_median_values_stay_white(self):
        self.assertIsNone(classify("ATACANTES", "COC_CHUTES", 16, 3))
        self.assertIsNone(classify("ATACANTES", "COC_AF", 30, 3))
        self.assertIsNone(classify("ATACANTES", "COC_PG", 2, 3))
        self.assertIsNone(classify("MEIAS", "COC_AF", 7, 3))
        self.assertIsNone(classify("LATERAIS", "COC_LE_DE", 5, 3))
        self.assertIsNone(classify("ZAGUEIROS", "COC_DE", 8, 3))

    def test_exact_boundaries_receive_color(self):
        self.assertEqual(classify("ATACANTES", "COC_CHUTES", 17, 3), "light")
        self.assertEqual(classify("ATACANTES", "COC_CHUTES", 20, 3), "medium")
        self.assertEqual(classify("ATACANTES", "COC_CHUTES", 23, 3), "dark")
        self.assertEqual(classify("ATACANTES", "COC_PG", 3, 3), "light")
        self.assertEqual(classify("ATACANTES", "COC_PG", 5, 3), "medium")
        self.assertEqual(classify("ATACANTES", "COC_PG", 7, 3), "dark")
        self.assertEqual(classify("MEIAS", "COC_AF", 8, 3), "light")
        self.assertEqual(classify("MEIAS", "COC_AF", 9, 3), "medium")
        self.assertEqual(classify("MEIAS", "COC_AF", 12, 3), "dark")

    def test_average_metrics_do_not_scale_with_window(self):
        self.assertEqual(classify("MEIAS", "COC_BASICA", 2.4, 3), "light")
        self.assertEqual(classify("MEIAS", "COC_BASICA", 2.4, 5), "light")

    def test_sum_metrics_scale_with_window(self):
        thresholds = get_thresholds("MEIAS", "COC_AF", 5)
        self.assertEqual((thresholds.light, thresholds.medium, thresholds.dark), (14, 15, 20))
        self.assertIsNone(classify("MEIAS", "COC_AF", 13, 5))
        self.assertEqual(classify("MEIAS", "COC_AF", 14, 5), "light")

    def test_no_quota_all_qualified_values_are_colored(self):
        values = [23] * 20
        self.assertTrue(all(classify("ATACANTES", "COC_CHUTES", v, 3) == "dark" for v in values))

    def test_laterals_share_one_conceptual_scale(self):
        self.assertEqual(classify("LATERAIS", "COC_LE_DE", 8, 3), "medium")
        self.assertEqual(classify("LATERAIS", "COC_LD_DE", 8, 3), "medium")

    def test_zagueiro_only_validated_metrics_receive_color(self):
        self.assertIsNone(classify("ZAGUEIROS", "COC_PTS", 12, 3))
        self.assertIsNone(classify("ZAGUEIROS", "COC_CHUTES_INDIV", 2, 3))
        self.assertEqual(classify("ZAGUEIROS", "COC_CHUTES_INDIV", 3, 3), "light")
        self.assertIsNone(classify("ZAGUEIROS", "COC_BASICA", 2.6, 3))
        self.assertEqual(classify("ZAGUEIROS", "COC_BASICA", 2.7, 3), "light")

    def test_conceded_is_colored_independently(self):
        weak_own = {"COC_AF": 7}
        strong_own = {"COC_AF": 9}
        self.assertEqual(classify_cell("MEIAS", "CDF_AF", 12, weak_own, 3), "dark")
        self.assertEqual(classify_cell("MEIAS", "CDF_AF", 12, strong_own, 3), "dark")

    def test_conceded_level_uses_its_own_value(self):
        row = {"COF_DE": 11}
        self.assertEqual(classify_cell("VOLANTES", "CDC_DE", 20, row, 3), "dark")


if __name__ == "__main__":
    unittest.main()
