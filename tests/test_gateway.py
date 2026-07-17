import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.gateway import GatewayError, ProviderTransportError, SimpleTrustedGateway
from trusted_data_demo.runtime import TrustedDataDemo


class RecordingProviderTransport:
    def __init__(self, unavailable=()):
        self.calls = []
        self.unavailable = set(unavailable)

    def execute(self, provider_id, envelope):
        self.calls.append((provider_id, envelope))
        if provider_id in self.unavailable:
            raise ProviderTransportError("provider_unavailable")
        score = 796 if provider_id == "grid" else 782
        return {
            "job_id": f"job_{provider_id}",
            "product_id": envelope["product_id"],
            "provider_id": provider_id,
            "status": "success",
            "result": {"credit_score": score, "provider_count": 1},
            "trace": [{"title": "provider executed", "actor": provider_id}],
            "receipt": None,
            "policy_decision": envelope["policy_decision"],
        }


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

    def test_gateway_fans_out_to_multiple_providers_without_aggregating(self):
        demo = TrustedDataDemo()
        transport = RecordingProviderTransport()
        gateway = SimpleTrustedGateway(demo, provider_transport=transport)
        bindings = []
        for provider_id in ("grid", "integrated-energy"):
            entitlement = demo.create_entitlement(
                product_id="enterprise-energy-credit",
                provider_id=provider_id,
                data_subject="91300000DEMO0007",
                requester_agent="agent:bank-risk",
            )
            bindings.append(
                {
                    "provider_id": provider_id,
                    "entitlement_id": entitlement["entitlement_id"],
                }
            )

        response = gateway.execute_action(
            {
                "request_id": "req_test_fanout",
                "requester_agent": "agent:bank-risk",
                "product_id": "enterprise-energy-credit",
                "product_version": "enterprise-energy-credit@1.0.0",
                "action_id": "compute_credit_features",
                "providers": bindings,
                "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            },
            api_key="demo_key_bank_agent",
        )

        self.assertEqual(response["status"], "completed")
        self.assertEqual(set(response["provider_results"]), {"grid", "integrated-energy"})
        self.assertEqual({call[0] for call in transport.calls}, {"grid", "integrated-energy"})
        self.assertNotIn("aggregated_credit_score", response)
        self.assertNotIn("result", response)

    def test_gateway_returns_partial_when_one_provider_entitlement_is_revoked(self):
        demo = TrustedDataDemo()
        transport = RecordingProviderTransport()
        gateway = SimpleTrustedGateway(demo, provider_transport=transport)
        grid = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )
        energy = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="integrated-energy",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )
        demo.revoke_entitlement(energy["entitlement_id"])

        response = gateway.execute_action(
            {
                "requester_agent": "agent:bank-risk",
                "product_id": "enterprise-energy-credit",
                "action_id": "compute_credit_features",
                "providers": [
                    {"provider_id": "grid", "entitlement_id": grid["entitlement_id"]},
                    {
                        "provider_id": "integrated-energy",
                        "entitlement_id": energy["entitlement_id"],
                    },
                ],
                "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            },
            api_key="demo_key_bank_agent",
        )

        self.assertEqual(response["status"], "partial")
        self.assertEqual(response["provider_results"]["grid"]["status"], "succeeded")
        denied = response["provider_results"]["integrated-energy"]
        self.assertEqual(denied["status"], "denied")
        self.assertEqual(denied["error_code"], "entitlement_revoked")
        self.assertEqual([call[0] for call in transport.calls], ["grid"])

    def test_gateway_rejects_duplicate_provider_bindings(self):
        demo = TrustedDataDemo()
        gateway = SimpleTrustedGateway(demo, provider_transport=RecordingProviderTransport())
        entitlement = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
            requester_agent="agent:bank-risk",
        )
        binding = {"provider_id": "grid", "entitlement_id": entitlement["entitlement_id"]}

        with self.assertRaises(GatewayError) as ctx:
            gateway.execute_action(
                {
                    "requester_agent": "agent:bank-risk",
                    "product_id": "enterprise-energy-credit",
                    "action_id": "compute_credit_features",
                    "providers": [binding, dict(binding)],
                    "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
                },
                api_key="demo_key_bank_agent",
            )

        self.assertEqual(ctx.exception.reason, "duplicate_provider_id:grid")

    def test_gateway_rejects_unknown_provider_before_dispatch(self):
        demo = TrustedDataDemo()
        transport = RecordingProviderTransport()
        gateway = SimpleTrustedGateway(demo, provider_transport=transport)

        with self.assertRaises(GatewayError) as ctx:
            gateway.execute_action(
                {
                    "requester_agent": "agent:bank-risk",
                    "product_id": "enterprise-energy-credit",
                    "action_id": "compute_credit_features",
                    "providers": [
                        {
                            "provider_id": "unknown-energy-provider",
                            "entitlement_id": "ent_unknown",
                        }
                    ],
                    "payload": {
                        "enterprise_id": "91300000DEMO0007",
                        "months": 12,
                    },
                },
                api_key="demo_key_bank_agent",
            )

        self.assertEqual(
            ctx.exception.reason,
            "provider_not_registered:unknown-energy-provider",
        )
        self.assertEqual(transport.calls, [])

    def test_gateway_isolates_provider_transport_failure(self):
        demo = TrustedDataDemo()
        gateway = SimpleTrustedGateway(
            demo,
            provider_transport=RecordingProviderTransport(
                unavailable={"integrated-energy"}
            ),
        )
        bindings = []
        for provider_id in ("grid", "integrated-energy"):
            entitlement = demo.create_entitlement(
                product_id="enterprise-energy-credit",
                provider_id=provider_id,
                data_subject="91300000DEMO0007",
                requester_agent="agent:bank-risk",
            )
            bindings.append(
                {
                    "provider_id": provider_id,
                    "entitlement_id": entitlement["entitlement_id"],
                }
            )

        response = gateway.execute_action(
            {
                "requester_agent": "agent:bank-risk",
                "product_id": "enterprise-energy-credit",
                "action_id": "compute_credit_features",
                "providers": bindings,
                "payload": {"enterprise_id": "91300000DEMO0007", "months": 12},
            },
            api_key="demo_key_bank_agent",
        )

        self.assertEqual(response["status"], "partial")
        self.assertEqual(response["provider_results"]["grid"]["status"], "succeeded")
        failed = response["provider_results"]["integrated-energy"]
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error_code"], "provider_unavailable")


if __name__ == "__main__":
    unittest.main()
