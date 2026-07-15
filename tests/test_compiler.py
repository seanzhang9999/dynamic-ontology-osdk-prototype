import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.compiler import CompileError, compile_product


class CompilerTests(unittest.TestCase):
    def test_power_product_hides_raw_and_compute_fields(self):
        package = compile_product("enterprise-energy-credit")
        manifest = package.product_manifest
        readable = {(item["object"], item["property"]) for item in manifest["readable_fields"]}

        self.assertIn("object_types", package.ontology_model)
        self.assertIn("EnergyUsage", package.ontology_model["object_types"])
        self.assertNotIn(("EnergyUsage", "raw_monthly_kwh"), readable)
        self.assertNotIn(("EnergyUsage", "kwh"), readable)
        self.assertIn("credit_score", package.product_schema["properties"])
        self.assertEqual(manifest["raw_export"], False)

    def test_forbidden_compute_field_cannot_be_added_to_output(self):
        with self.assertRaises(CompileError):
            compile_product("enterprise-energy-credit", extra_outputs=["EnergyUsage.kwh"])

    def test_coordinate_core_recompile_removes_coordinate_read_surface(self):
        before = compile_product("changchun-excavation-risk", coordinate_core=False)
        after = compile_product("changchun-excavation-risk", coordinate_core=True)

        before_readable = {
            (item["object"], item["property"]) for item in before.product_manifest["readable_fields"]
        }
        after_readable = {
            (item["object"], item["property"]) for item in after.product_manifest["readable_fields"]
        }

        self.assertNotIn(("PipelineSegment", "exact_coordinates"), after_readable)
        self.assertIn("assess_excavation_risk", after.product_manifest["actions"])
        self.assertEqual(after.product_manifest["version"], "1.1.0")
        self.assertEqual(before.product_manifest["id"], after.product_manifest["id"])


if __name__ == "__main__":
    unittest.main()
