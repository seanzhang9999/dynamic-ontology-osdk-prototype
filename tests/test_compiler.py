import pathlib
import sys
import unittest
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.compiler import (
    CompileError,
    compile_product,
    write_python_sdk_packages,
)


class CompilerTests(unittest.TestCase):
    def test_power_product_hides_raw_and_compute_fields(self):
        package = compile_product("enterprise-energy-credit")
        manifest = package.product_manifest
        readable = {(item["object"], item["property"]) for item in manifest["readable_fields"]}

        self.assertIn("object_types", package.ontology_model)
        self.assertIn("EnergyUsage", package.ontology_model["object_types"])
        self.assertIn("EnterpriseUsage", package.ontology_model["link_types"])
        self.assertNotIn(("EnergyUsage", "raw_monthly_kwh"), readable)
        self.assertNotIn(("EnergyUsage", "kwh"), readable)
        self.assertIn("credit_score", package.product_schema["properties"])
        self.assertIn("enterprise_id: str", package.python_osdk)
        self.assertIn("entitlement_id: str", package.python_osdk)
        self.assertIn("ProviderRuntimeClient", package.python_osdk)
        self.assertIn("ProviderBinding", package.python_osdk)
        self.assertIn("providers: List[ProviderBinding]", package.python_osdk)
        self.assertIn("ComputeCreditFeaturesMultiProviderResult", package.python_osdk)
        self.assertIn("action_id='compute_credit_features'", package.python_osdk)
        self.assertNotIn("def compute_credit_features(self, **payload)", package.python_osdk)
        self.assertIn("provider_id", package.action_schemas["compute_credit_features"]["inputs"])
        self.assertIn("ComputeCreditFeaturesInput", package.sdk_files["enterprise_energy_credit/models.py"])
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
        self.assertIn("excavation_area: Dict[str, Any]", after.python_osdk)
        self.assertIn("action_id='assess_excavation_risk'", after.python_osdk)
        self.assertEqual(after.product_manifest["version"], "1.1.0")
        self.assertEqual(before.product_manifest["id"], after.product_manifest["id"])

    def test_sdk_package_files_are_generated(self):
        package = compile_product("enterprise-energy-credit")
        self.assertIn("pyproject.toml", package.sdk_files)
        self.assertIn("enterprise_energy_credit/client.py", package.sdk_files)
        self.assertIn("enterprise_energy_credit/runtime.py", package.sdk_files)
        self.assertIn("ProviderRuntimeClient", package.sdk_files["enterprise_energy_credit/runtime.py"])
        self.assertIn('requires-python = ">=3.10"', package.sdk_files["pyproject.toml"])

    def test_generated_sdk_package_can_be_imported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_python_sdk_packages(tmpdir)
            sys.path.insert(0, str(pathlib.Path(written["enterprise-energy-credit"])))
            try:
                from enterprise_energy_credit import (  # type: ignore
                    ComputeCreditFeaturesMultiProviderResult,
                    EnterpriseEnergyCreditClient,
                    ProviderBinding,
                    ProviderRuntimeClient,
                )

                self.assertEqual(EnterpriseEnergyCreditClient.__name__, "EnterpriseEnergyCreditClient")
                self.assertEqual(ProviderRuntimeClient.__name__, "ProviderRuntimeClient")
                self.assertEqual(ProviderBinding.__name__, "ProviderBinding")
                self.assertEqual(
                    ComputeCreditFeaturesMultiProviderResult.__name__,
                    "ComputeCreditFeaturesMultiProviderResult",
                )

                class FakeGatewayRuntime:
                    def execute_action(self, **kwargs):
                        self.kwargs = kwargs
                        return {
                            "request_id": "req_generated_sdk_test",
                            "status": "completed",
                            "product_id": "enterprise-energy-credit",
                            "action_id": "compute_credit_features",
                            "provider_results": {
                                "grid": {
                                    "provider_id": "grid",
                                    "status": "succeeded",
                                    "result": {"credit_score": 796},
                                    "error_code": None,
                                    "receipt_id": "req_receipt_grid",
                                    "runtime_version": "grid-runtime@0.1.0",
                                    "job_id": "job_grid",
                                    "policy_decision": "allowed",
                                    "runtime_trace": [],
                                    "receipt": None,
                                }
                            },
                            "gateway": {},
                            "trace": [],
                        }

                runtime = FakeGatewayRuntime()
                client = EnterpriseEnergyCreditClient(runtime=runtime)
                response = client.compute_credit_features(
                    providers=[
                        ProviderBinding(provider_id="grid", entitlement_id="ent_grid")
                    ],
                    enterprise_id="91300000DEMO0007",
                    months=12,
                )
                self.assertEqual(response.provider_results["grid"].result.credit_score, 796)
                self.assertEqual(runtime.kwargs["providers"][0]["provider_id"], "grid")
            finally:
                sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
