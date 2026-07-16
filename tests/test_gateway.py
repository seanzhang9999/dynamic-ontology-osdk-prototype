import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.gateway import GatewayError, SimpleTrustedGateway
from trusted_data_demo.runtime import TrustedDataDemo


class GatewayTests(unittest.TestCase):
    def test_remote_osdk_envelope_executes_through_gateway(self):
        demo = TrustedDataDemo()
        gateway = SimpleTrustedGateway(demo)
        entitlement = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )
        product = demo.products["enterprise-energy-credit"]["product_manifest"]

        response = gateway.execute_action(
            {
                "request_id": "req_test_gateway",
                "requester_agent": "agent:bank-risk",
                "provider_id": "grid",
                "product_id": "enterprise-energy-credit",
                "product_version": product["product_version"],
                "action_id": "compute_credit_features",
                "entitlement_id": entitlement["entitlement_id"],
                "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            },
            api_key="demo_key_bank_agent",
        )

        self.assertEqual(response["status"], "succeeded")
        self.assertIn("credit_score", response["result"])
        self.assertTrue(response["receipt_id"].startswith("req_"))
        self.assertIn("runtime_trace", response)
        self.assertIn("Gateway 校验产品契约", [step["title"] for step in response["trace"]])

    def test_gateway_rejects_revoked_entitlement_before_runtime_route(self):
        demo = TrustedDataDemo()
        gateway = SimpleTrustedGateway(demo)
        entitlement = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )
        demo.revoke_entitlement(entitlement["entitlement_id"])
        product = demo.products["enterprise-energy-credit"]["product_manifest"]

        response = gateway.execute_action(
            {
                "requester_agent": "agent:bank-risk",
                "provider_id": "grid",
                "product_id": "enterprise-energy-credit",
                "product_version": product["product_version"],
                "action_id": "compute_credit_features",
                "entitlement_id": entitlement["entitlement_id"],
                "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            },
            api_key="demo_key_bank_agent",
        )

        self.assertEqual(response["status"], "denied")
        self.assertEqual(response["reason"], "entitlement_revoked")

    def test_gateway_rejects_unknown_payload_fields(self):
        demo = TrustedDataDemo()
        gateway = SimpleTrustedGateway(demo)
        entitlement = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )

        with self.assertRaises(GatewayError) as ctx:
            gateway.execute_action(
                {
                    "requester_agent": "agent:bank-risk",
                    "provider_id": "grid",
                    "product_id": "enterprise-energy-credit",
                    "action_id": "compute_credit_features",
                    "entitlement_id": entitlement["entitlement_id"],
                    "payload": {
                        "enterprise_id": "91300000DEMO0007",
                        "months": 12,
                        "raw_sql": "select * from monthly_usage",
                    },
                },
                api_key="demo_key_bank_agent",
            )

        self.assertIn("unknown_payload_fields", ctx.exception.reason)


if __name__ == "__main__":
    unittest.main()
