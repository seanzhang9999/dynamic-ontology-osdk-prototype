import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.audit import AuditLog
from trusted_data_demo.models import PolicyDecision
from trusted_data_demo.provider_app import ProviderRuntimeError, ProviderRuntimeService


class ProviderRuntimeServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ProviderRuntimeService(
            provider_id="grid",
            internal_key="test-internal-key",
        )
        self.envelope = {
            "request_id": "req_provider_test",
            "requester_agent": "agent:bank-risk",
            "provider_id": "grid",
            "product_id": "enterprise-energy-credit",
            "product_version": "enterprise-energy-credit@1.0.0",
            "action_id": "compute_credit_features",
            "entitlement_id": "ent_test",
            "purpose": "enterprise_credit_assessment",
            "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            "policy_decision": PolicyDecision(
                allowed=True,
                reason="allowed",
                output_granularity="enterprise-feature-summary",
                entitlement_id="ent_test",
            ).model_dump(mode="json"),
        }

    def test_runtime_loads_only_its_provider_dataset(self):
        self.assertEqual(set(self.service.runtime.power_data), {"grid"})
        self.assertEqual(self.service.runtime.changchun_assets, {})

    def test_runtime_rejects_missing_internal_gateway_key(self):
        with self.assertRaises(ProviderRuntimeError) as ctx:
            self.service.execute(self.envelope, gateway_key=None)

        self.assertEqual(ctx.exception.reason, "invalid_gateway_key")

    def test_runtime_rejects_provider_scope_mismatch(self):
        envelope = dict(self.envelope)
        envelope["provider_id"] = "integrated-energy"

        with self.assertRaises(ProviderRuntimeError) as ctx:
            self.service.execute(envelope, gateway_key="test-internal-key")

        self.assertEqual(ctx.exception.reason, "provider_scope_mismatch")

    def test_runtime_rejects_invalid_policy_decision(self):
        envelope = dict(self.envelope)
        envelope["policy_decision"] = {}

        with self.assertRaises(ProviderRuntimeError) as ctx:
            self.service.execute(envelope, gateway_key="test-internal-key")

        self.assertEqual(ctx.exception.reason, "invalid_policy_decision")

    def test_runtime_executes_gateway_authorized_action_and_signs_receipt(self):
        response = self.service.execute(
            self.envelope,
            gateway_key="test-internal-key",
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["provider_id"], "grid")
        self.assertIn("credit_score", response["result"])
        self.assertNotIn("kwh", response["result"])
        self.assertTrue(AuditLog.verify(response["receipt"]))


if __name__ == "__main__":
    unittest.main()
