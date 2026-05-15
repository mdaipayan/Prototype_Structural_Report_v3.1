import unittest

from design_calcs import LoadInputs, ZSectionInputs, code_checks, z_section_properties


class CodeChecksTest(unittest.TestCase):
    def test_minimum_depth_check_compares_clear_web_to_required_depth(self):
        inp = LoadInputs()
        sec = ZSectionInputs(t_mm=2.5, overall_depth_D_mm=250.0)
        props = z_section_properties(sec)

        checks = code_checks(
            inp, sec, props, support_moment_kg_m=0.0, span_moment_kg_m=0.0
        )

        self.assertAlmostEqual(props["d_clear_mm"], 245.0)
        self.assertAlmostEqual(checks["minimum_depth_required_mm"], 12.0)
        self.assertTrue(checks["minimum_depth_check_ok"])

    def test_minimum_depth_check_fails_when_clear_web_is_too_shallow(self):
        inp = LoadInputs()
        sec = ZSectionInputs(t_mm=2.5, overall_depth_D_mm=14.0)
        props = z_section_properties(sec)

        checks = code_checks(
            inp, sec, props, support_moment_kg_m=0.0, span_moment_kg_m=0.0
        )

        self.assertLess(props["d_clear_mm"], checks["minimum_depth_required_mm"])
        self.assertFalse(checks["minimum_depth_check_ok"])


if __name__ == "__main__":
    unittest.main()
