# -*- coding: utf-8 -*-
import unittest
from harness_core.measurement_utils import bootstrap_ci, cohen_kappa, krippendorff_alpha


class MeasurementUtilsTest(unittest.TestCase):
    def test_bootstrap_ci(self):
        ci = bootstrap_ci([0.5, 0.6, 0.7, 0.8, 0.9])
        self.assertIsNotNone(ci)
        self.assertTrue(0.6 <= ci["mean"] <= 0.7)

    def test_cohen_kappa_perfect(self):
        self.assertEqual(cohen_kappa([1, 2, 3, 4], [1, 2, 3, 4]), 1.0)

    def test_cohen_kappa_random(self):
        k = cohen_kappa([1, 1, 2, 2, 3, 3], [1, 2, 2, 3, 3, 3])
        self.assertIsNotNone(k)
        self.assertLessEqual(k, 1.0)

    def test_krippendorff_perfect_agreement(self):
        alpha = krippendorff_alpha([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
        self.assertIsNotNone(alpha)
        self.assertAlmostEqual(alpha, 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
