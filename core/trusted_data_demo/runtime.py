from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, Dict, List
from uuid import uuid4

from .audit import AuditLog, sha256_json
from .compiler import compile_all, compile_product
from .fixtures import PROVIDERS, make_changchun_assets, make_power_records
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
            "product_packages": self.products,
            "entitlements": {
                key: entitlement.model_dump(mode="json")
                for key, entitlement in self.policy.all().items()
            },
            "jobs": {key: job.model_dump(mode="json") for key, job in self.jobs.items()},
            "audit_events": self.audit.events(),
            "coordinate_core": self.coordinate_core,
            "enterprise_options": self.enterprise_options(),
        }

    def enterprise_options(self) -> List[Dict[str, Any]]:
        enterprise_ids = sorted(
            {record["enterprise_id"] for record in self.power_data["grid"]}
        )
        return [
            {
                "id": enterprise_id,
                "name": f"示例企业 {enterprise_id[-4:]}",
                "description": "合成企业，用于演示授权后企业用电征信查询",
            }
            for enterprise_id in enterprise_ids[:24]
        ]

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
                trace=[
                    {
                        "title": "Policy 拒绝执行",
                        "actor": "Policy Service",
                        "detail": f"授权校验失败：{decision.reason}",
                        "facts": {"entitlement_id": entitlement_id},
                    }
                ],
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
        product_package = self.products[product_id]
        source_mapping = {
            "grid": {
                "EnergyUsage.kwh": "monthly_usage.total_kwh",
                "BillingRecord.late_days": "paid_date - due_date",
                "Enterprise.enterprise_id": "customer.unified_credit_code",
            },
            "integrated-energy": {
                "EnergyUsage.kwh": "billing.energy_qty",
                "BillingRecord.late_days": "settle_date - deadline",
                "Enterprise.enterprise_id": "enterprise.enterprise_no",
            },
        }[provider_id]
        trace = [
            {
                "title": "前端选择企业并发起查询",
                "actor": "Demo Console",
                "detail": "用户选择企业后，前端只提交企业 ID 和用途请求，不提交 SQL 或底层字段。",
                "facts": {
                    "enterprise_id": enterprise_id,
                    "product": product_id,
                    "months": months,
                },
            },
            {
                "title": "应用获得 Product OSDK 调用面",
                "actor": "Generated OSDK",
                "detail": "OSDK 由动态本体和产品投影生成，只暴露命名动作。",
                "code": product_package["python_osdk"],
            },
            {
                "title": "OSDK 调用动态本体动作",
                "actor": "Product OSDK",
                "detail": "compute_credit_features 绑定到本体动作，动作声明了内部依赖字段。",
                "facts": product_package["runtime_binding"]["internal_dependencies"][
                    "compute_credit_features"
                ],
            },
            {
                "title": "Runtime 将本体字段映射到底层数据",
                "actor": PROVIDERS[provider_id]["display_name"],
                "detail": "映射只在 Provider 数据域内使用，外部应用看不到表名和连接信息。",
                "facts": source_mapping,
            },
            {
                "title": "Provider 本地扫描并计算特征",
                "actor": "Provider Runtime",
                "detail": "Runtime 在本地读取合成明细行，计算稳定性和逾期区间；原始行不进入响应。",
                "facts": {
                    "local_rows_scanned": len(records),
                    "data_window": f"{records[0]['period']}..{records[-1]['period']}"
                    if records
                    else "empty",
                    "compute_only_fields": ["EnergyUsage.kwh", "BillingRecord.late_days"],
                },
            },
            {
                "title": "输出过滤为产品 schema",
                "actor": "Output Filter",
                "detail": "只返回 EXTERNAL_RESULT 或允许的摘要字段，隐藏原始用电序列和缴费流水。",
                "facts": {
                    "returned_fields": list(result.keys()),
                    "blocked_fields": ["raw_monthly_kwh", "kwh", "source_row_id"],
                },
            },
        ]
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
            trace=trace,
            receipt=receipt,
            policy_decision=decision,
        )
        job.trace.append(
            {
                "title": "生成执行凭证",
                "actor": "Audit Service",
                "detail": "凭证记录授权、应用、本体、映射、产品版本、输入输出 hash，并用 Ed25519 签名。",
                "facts": {
                    "receipt_id": receipt.request_id,
                    "input_hash": receipt.input_hash,
                    "output_hash": receipt.output_hash,
                    "signature_algorithm": receipt.signature_algorithm,
                },
            }
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
