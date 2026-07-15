import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from trusted_data_demo.audit import AuditLog
from trusted_data_demo.runtime import TrustedDataDemo


class RuntimePolicyAuditTests(unittest.TestCase):
    def test_power_credit_runs_on_two_providers_without_raw_rows(self):
        demo = TrustedDataDemo()
        result = demo.run_power_credit_demo("91300000DEMO0007")
        jobs = result["jobs"]

        self.assertEqual(len(jobs), 2)
        self.assertEqual({job["status"] for job in jobs}, {"success"})
        result_keys = set(jobs[0]["result"].keys())
        self.assertIn("credit_score", result_keys)
        self.assertIn("late_payment_count_band", result_keys)
        self.assertNotIn("raw_monthly_kwh", result_keys)
        self.assertNotIn("kwh", result_keys)
        self.assertTrue(AuditLog.verify(jobs[0]["receipt"]))

    def test_revoked_entitlement_denies_runtime_execution(self):
        demo = TrustedDataDemo()
        entitlement = demo.create_entitlement(
            product_id="enterprise-energy-credit",
            provider_id="grid",
            data_subject="91300000DEMO0007",
        )
        demo.revoke_entitlement(entitlement["entitlement_id"])
        job = demo.execute_power_credit(
            provider_id="grid",
            enterprise_id="91300000DEMO0007",
            entitlement_id=entitlement["entitlement_id"],
        )

        self.assertEqual(job.status, "denied")
        self.assertEqual(job.policy_decision.reason, "entitlement_revoked")

    def test_receipt_tampering_fails_verification(self):
        demo = TrustedDataDemo()
        result = demo.run_power_credit_demo("91300000DEMO0007")
        receipt = dict(result["jobs"][0]["receipt"])

        self.assertTrue(AuditLog.verify(receipt))
        receipt["output_hash"] = "sha256:tampered"
        self.assertFalse(AuditLog.verify(receipt))

    def test_changchun_runtime_outputs_summary_not_coordinates(self):
        demo = TrustedDataDemo()
        demo.recompile_coordinate_core()
        job = demo.run_changchun_demo()

        self.assertEqual(job["status"], "success")
        self.assertIn("overall_risk", job["result"])
        self.assertIn("affected_segment_count", job["result"])
        self.assertNotIn("exact_coordinates", job["result"])
        self.assertNotIn("segment_id", job["result"])
        self.assertTrue(AuditLog.verify(job["receipt"]))


if __name__ == "__main__":
    unittest.main()

