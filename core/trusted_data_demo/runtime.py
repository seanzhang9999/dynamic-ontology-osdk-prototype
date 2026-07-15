from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Any, Dict, List
from uuid import uuid4

from .audit import AuditLog, sha256_json
from .compiler import compile_all, compile_product
from .fixtures import PROVIDERS, make_changchun_assets, make_power_records, product_definitions
from .geo import bbox_intersects, expand_bbox, line_bbox, polygon_bbox
from .models import ApplicationManifest, ExecutionJob, PolicyDecision
from .policy import EntitlementStore


DEFAULT_APP = ApplicationManifest(
    app_id="bank-risk-app",
    version="1.0.0",
    digest="sha256:bank-risk-app-demo",
    requester_agent="agent:bank-risk",
    allowed_products=["enterprise-energy-credit", "changchun-excavation-risk"],
)

CHANGCHUN_APP = ApplicationManifest(
    app_id="excavation-risk-app",
    version="1.0.0",
    digest="sha256:excavation-risk-app-demo",
    requester_agent="agent:construction-safety",
    allowed_products=["changchun-excavation-risk"],
)


class TrustedDataDemo:
    def __init__(self) -> None:
        self.policy = EntitlementStore()
        self.audit = AuditLog()
        self.power_data = {
            "grid": make_power_records("grid"),
            "integrated-energy": make_power_records("integrated-energy"),
        }
        self.changchun_assets = make_changchun_assets()
        self.coordinate_core = False
        self.products = compile_all(coordinate_core=self.coordinate_core)
        self.jobs: Dict[str, ExecutionJob] = {}

    def state(self) -> Dict[str, Any]:
        return {
            "products": {
                product_id: package["product_manifest"]
                for product_id, package in self.products.items()
            },
            "entitlements": {
                key: entitlement.model_dump(mode="json")
                for key, entitlement in self.policy.all().items()
            },
            "jobs": {key: job.model_dump(mode="json") for key, job in self.jobs.items()},
            "audit_events": self.audit.events(),
            "coordinate_core": self.coordinate_core,
        }

    def recompile_coordinate_core(self) -> Dict[str, Any]:
        self.coordinate_core = True
        self.products["changchun-excavation-risk"] = compile_product(
            "changchun-excavation-risk", coordinate_core=True
        ).model_dump(mode="json")
        return self.products["changchun-excavation-risk"]

    def create_entitlement(
        self,
        *,
        product_id: str,
        provider_id: str,
        data_subject: str,
        requester_agent: str = DEFAULT_APP.requester_agent,
    ) -> Dict[str, Any]:
        product = self.products[product_id]["product_manifest"]
        entitlement = self.policy.create(
            product_id=product_id,
            purpose=product["purpose"],
            requester_agent=requester_agent,
            data_subject=data_subject,
            provider_id=provider_id,
            output_granularity=product["output_granularity"],
            expires_hours=24,
            max_calls=10,
        )
        return entitlement.model_dump(mode="json")

    def revoke_entitlement(self, entitlement_id: str) -> Dict[str, Any]:
        return self.policy.revoke(entitlement_id).model_dump(mode="json")

    def _policy_decision(
        self,
        *,
        entitlement_id: str,
        product_id: str,
        provider_id: str,
        app: ApplicationManifest,
    ) -> PolicyDecision:
        product = self.products[product_id]["product_manifest"]
        if product_id not in app.allowed_products:
            return PolicyDecision(allowed=False, reason="application_product_not_allowed")
        return self.policy.evaluate(
            entitlement_id=entitlement_id,
            product_id=product_id,
            purpose=product["purpose"],
            requester_agent=app.requester_agent,
            provider_id=provider_id,
            output_granularity=product["output_granularity"],
        )

    def execute_power_credit(
        self,
        *,
        provider_id: str,
        enterprise_id: str,
        entitlement_id: str,
        app: ApplicationManifest = DEFAULT_APP,
        months: int = 12,
    ) -> ExecutionJob:
        product_id = "enterprise-energy-credit"
        decision = self._policy_decision(
            entitlement_id=entitlement_id,
            product_id=product_id,
            provider_id=provider_id,
            app=app,
        )
        if not decision.allowed:
            job = ExecutionJob(
                job_id=f"job_{uuid4().hex[:12]}",
                product_id=product_id,
                provider_id=provider_id,
                status="denied",
                policy_decision=decision,
            )
            self.jobs[job.job_id] = job
            return job

        records = [
            record
            for record in self.power_data[provider_id]
            if record["enterprise_id"] == enterprise_id
        ][-months:]
        kwh_values = [record["kwh"] for record in records]
        late_count = sum(1 for record in records if record["late_days"] > 0)
        coverage_months = len(records)
        average_kwh = mean(kwh_values) if kwh_values else 0
        stability = 1 - (pstdev(kwh_values) / average_kwh if average_kwh else 1)
        stability = max(0, min(1, round(stability, 4)))
        score = round(620 + stability * 180 - late_count * 18 + min(coverage_months, 12) * 3)
        risk_level = "low" if score >= 760 else "medium" if score >= 680 else "high"
        late_band = "0" if late_count == 0 else "1-2" if late_count <= 2 else "3+"
        result = {
            "credit_score": score,
            "risk_level": risk_level,
            "coverage_months": coverage_months,
            "usage_stability_index": stability,
            "late_payment_count_band": late_band,
            "provider_count": 1,
            "quality_summary": {
                "missing_rate": 0.0,
                "coverage_months": coverage_months,
                "quality_gate": "passed" if coverage_months >= 12 else "warning",
            },
            "explanation": (
                f"{PROVIDERS[provider_id]['display_name']} returned purpose-bound "
                f"feature summary for {coverage_months} months; raw usage rows stayed local."
            ),
        }
        product = self.products[product_id]["product_manifest"]
        receipt = self.audit.create_receipt(
            purpose=product["purpose"],
            requester_agent=app.requester_agent,
            provider_agent=PROVIDERS[provider_id]["provider_agent"],
            data_subject=enterprise_id,
            consent_digest=sha256_json({"entitlement_id": entitlement_id}),
            entitlement_id=entitlement_id,
            application_digest=app.digest,
            ontology_version=product["ontology"]["id"] + "@" + product["ontology"]["version"],
            mapping_version=PROVIDERS[provider_id]["mapping_version"],
            product_version=product["product_version"],
            runtime_version=f"{provider_id}-runtime@0.1.0",
            data_window=f"{records[0]['period']}..{records[-1]['period']}" if records else "empty",
            quality_snapshot=result["quality_summary"],
            request_payload={"enterprise_id": enterprise_id, "months": months},
            output_payload=result,
            policy_decision=decision,
        )
        job = ExecutionJob(
            job_id=f"job_{uuid4().hex[:12]}",
            product_id=product_id,
            provider_id=provider_id,
            status="success",
            result=result,
            receipt=receipt,
            policy_decision=decision,
        )
        self.jobs[job.job_id] = job
        return job

    def run_power_credit_demo(self, enterprise_id: str = "91300000DEMO0007") -> Dict[str, Any]:
        jobs = []
        for provider_id in ("grid", "integrated-energy"):
            entitlement = self.create_entitlement(
                product_id="enterprise-energy-credit",
                provider_id=provider_id,
                data_subject=enterprise_id,
            )
            jobs.append(
                self.execute_power_credit(
                    provider_id=provider_id,
                    enterprise_id=enterprise_id,
                    entitlement_id=entitlement["entitlement_id"],
                )
            )
        scores = [job.result["credit_score"] for job in jobs if job.result]
        aggregate = {
            "enterprise_id": enterprise_id,
            "provider_count": len(scores),
            "aggregated_credit_score": round(mean(scores), 2) if scores else None,
            "risk_level": "low"
            if scores and mean(scores) >= 760
            else "medium"
            if scores and mean(scores) >= 680
            else "high",
            "jobs": [job.model_dump(mode="json") for job in jobs],
        }
        return aggregate

    def execute_changchun_risk(
        self,
        *,
        entitlement_id: str,
        excavation_area: Dict[str, Any],
        excavation_depth: float,
        construction_method: str,
        project_id: str,
        app: ApplicationManifest = CHANGCHUN_APP,
    ) -> ExecutionJob:
        product_id = "changchun-excavation-risk"
        provider_id = "changchun"
        decision = self._policy_decision(
            entitlement_id=entitlement_id,
            product_id=product_id,
            provider_id=provider_id,
            app=app,
        )
        if not decision.allowed:
            job = ExecutionJob(
                job_id=f"job_{uuid4().hex[:12]}",
                product_id=product_id,
                provider_id=provider_id,
                status="denied",
                policy_decision=decision,
            )
            self.jobs[job.job_id] = job
            return job

        area_bbox = expand_bbox(polygon_bbox(excavation_area), 0.004)
        affected = []
        for segment in self.changchun_assets["pipeline_segments"]:
            if bbox_intersects(area_bbox, line_bbox(segment["line"])):
                affected.append(segment)
        asset_types = sorted({segment["asset_type"] for segment in affected})
        depth_factor = 1.2 if excavation_depth >= 3 else 1.0
        method_factor = 1.25 if construction_method.upper() == "MECHANICAL" else 0.9
        risk_score = sum(segment["risk_weight"] for segment in affected) * depth_factor * method_factor
        if risk_score >= 2.2:
            overall_risk = "high"
        elif risk_score >= 1.1:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        result = {
            "overall_risk": overall_risk,
            "affected_asset_types": asset_types,
            "affected_segment_count": len(affected),
            "recommendations": [
                "Require utility owner confirmation before excavation",
                "Use manual potholing near high-risk assets",
                "Keep monitoring alerts active during construction",
            ]
            if affected
            else ["No critical buried utility conflict found in demo data"],
            "quality_summary": {
                "spatial_rule": "bbox-buffer-demo",
                "monitoring_quality_min": min(
                    item["quality"]
                    for item in self.changchun_assets["monitoring_summary"].values()
                ),
                "quality_gate": "passed",
            },
        }
        product = self.products[product_id]["product_manifest"]
        receipt = self.audit.create_receipt(
            purpose=product["purpose"],
            requester_agent=app.requester_agent,
            provider_agent=PROVIDERS[provider_id]["provider_agent"],
            data_subject=project_id,
            consent_digest=sha256_json({"entitlement_id": entitlement_id}),
            entitlement_id=entitlement_id,
            application_digest=app.digest,
            ontology_version=product["ontology"]["id"] + "@" + product["ontology"]["version"],
            mapping_version=PROVIDERS[provider_id]["mapping_version"],
            product_version=product["product_version"],
            runtime_version="changchun-runtime@0.1.0",
            data_window="2026-Q2",
            quality_snapshot=result["quality_summary"],
            request_payload={
                "project_id": project_id,
                "excavation_depth": excavation_depth,
                "construction_method": construction_method,
            },
            output_payload=result,
            policy_decision=decision,
        )
        job = ExecutionJob(
            job_id=f"job_{uuid4().hex[:12]}",
            product_id=product_id,
            provider_id=provider_id,
            status="success",
            result=result,
            receipt=receipt,
            policy_decision=decision,
        )
        self.jobs[job.job_id] = job
        return job

    def run_changchun_demo(self) -> Dict[str, Any]:
        product_id = "changchun-excavation-risk"
        project_id = "CC-2026-001"
        entitlement = self.create_entitlement(
            product_id=product_id,
            provider_id="changchun",
            data_subject=project_id,
            requester_agent=CHANGCHUN_APP.requester_agent,
        )
        area = {
            "type": "Polygon",
            "coordinates": [
                [
                    [125.313, 43.883],
                    [125.322, 43.883],
                    [125.322, 43.891],
                    [125.313, 43.891],
                    [125.313, 43.883],
                ]
            ],
        }
        job = self.execute_changchun_risk(
            entitlement_id=entitlement["entitlement_id"],
            excavation_area=area,
            excavation_depth=3.5,
            construction_method="MECHANICAL",
            project_id=project_id,
            app=CHANGCHUN_APP,
        )
        return job.model_dump(mode="json")

    def get_job(self, job_id: str) -> ExecutionJob:
        return self.jobs[job_id]

    def get_receipt(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs[job_id]
        if not job.receipt:
            raise KeyError(f"Job {job_id} does not have a receipt")
        return job.receipt.model_dump(mode="json")
