import unittest

from design_calcs import (
    LoadInputs,
    ZPurlinASDInputs,
    ZSectionInputs,
    code_checks,
    z_purlin_design_analysis,
    z_purlin_design_moments,
    z_purlin_flat_width_checks,
    z_purlin_resolved_loads,
    z_section_properties,
)


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


class ZPurlinASDWorkflowTest(unittest.TestCase):
    def test_flat_width_checks_match_preliminary_limits(self):
        checks = z_purlin_flat_width_checks(ZPurlinASDInputs())

        self.assertAlmostEqual(checks["web_flat_width_mm"], 196.0)
        self.assertAlmostEqual(checks["web_ratio"], 98.0)
        self.assertTrue(checks["web_ratio_ok"])
        self.assertAlmostEqual(checks["flange_flat_width_mm"], 56.0)
        self.assertAlmostEqual(checks["flange_ratio"], 28.0)
        self.assertTrue(checks["flange_ratio_ok"])

    def test_load_resolution_and_moments_follow_asd_framework(self):
        inputs = ZPurlinASDInputs()

        loads = z_purlin_resolved_loads(inputs)
        moments = z_purlin_design_moments(inputs, loads)

        self.assertAlmostEqual(loads["gravity_line_load_kn_m"], 1.08)
        self.assertAlmostEqual(loads["gravity_normal_kn_m"], 1.063592, places=6)
        self.assertAlmostEqual(loads["gravity_tangential_kn_m"], 0.187540, places=6)
        self.assertAlmostEqual(loads["uplift_line_load_kn_m"], -1.62)
        self.assertAlmostEqual(moments["gravity_major_axis_kn_m"], 2.658981, places=6)
        self.assertAlmostEqual(moments["gravity_minor_axis_kn_m"], 0.586063, places=6)
        self.assertAlmostEqual(moments["uplift_major_axis_kn_m"], -3.988471, places=6)

    def test_design_analysis_returns_design_interaction_status(self):
        inputs = ZPurlinASDInputs()
        loads = z_purlin_resolved_loads(inputs)
        moments = z_purlin_design_moments(inputs, loads)

        design = z_purlin_design_analysis(inputs, moments)

        self.assertGreater(design["zxx_effective_cm3"], 0.0)
        self.assertGreater(design["zyy_effective_cm3"], 0.0)
        self.assertAlmostEqual(design["allowable_stress_n_mm2"], 150.0)
        self.assertIn("gravity_interaction_ok", design)
        self.assertIn("uplift_interaction_ok", design)


class AdvancedChecksTest(unittest.TestCase):
    def test_deflection_calculation_uses_consistent_kn_m_and_cm4_units(self):
        from advanced_checks import deflection_calculation

        # Simply supported beam: delta = 5wL^4/(384EI). 1 kN/m = 1 N/mm,
        # and 100 cm^4 = 1,000,000 mm^4, giving about 39.698 mm.
        self.assertAlmostEqual(
            deflection_calculation(
                load_kn_m=1.0,
                span_m=5.0,
                moment_of_inertia_cm4=100.0,
                support_condition="simply_supported",
            ),
            39.698,
            places=3,
        )


class StreamlitPageStructureTest(unittest.TestCase):
    def test_only_purlin_design_page_is_registered(self):
        from pathlib import Path

        page_names = sorted(path.name for path in Path("pages").glob("*.py"))

        self.assertEqual(page_names, ["1_Purlin_Design.py"])


if __name__ == "__main__":
    unittest.main()
