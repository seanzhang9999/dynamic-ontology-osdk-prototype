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
            "source_tables": self.source_tables(),
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

    def _power_osdk_code(
        self,
        *,
        product_package: Dict[str, Any],
        enterprise_id: str,
        months: int,
        entitlement_id: str,
    ) -> str:
        return (
            product_package["python_osdk"]
            + "\n\n"
            + "# 智能体 Agent 实际调用：只传业务参数和授权句柄，不传 SQL、表名或连接串\n"
            + "# entitlement_id 是 Policy Service 签发的授权许可编号，限定用途、Provider、数据主体、期限和配额\n"
            + "client = EnterpriseEnergyCreditClient(runtime=provider_runtime)\n"
            + "credit_result = client.compute_credit_features(\n"
            + f"    enterprise_id=\"{enterprise_id}\",\n"
            + f"    months={months},\n"
            + f"    entitlement_id=\"{entitlement_id}\",\n"
            + ")\n"
        )

    def _changchun_osdk_code(
        self,
        *,
        product_package: Dict[str, Any],
        project_id: str,
        excavation_depth: float,
        construction_method: str,
        entitlement_id: str,
    ) -> str:
        return (
            product_package["python_osdk"]
            + "\n\n"
            + "# 智能体 Agent 实际调用：提交工程参数和区域，坐标/管线明细留在 Runtime 内部\n"
            + "# entitlement_id 是 Policy Service 签发的授权许可编号，限定用途、Provider、工程主体、期限和配额\n"
            + "client = ChangchunExcavationRiskClient(runtime=changchun_runtime)\n"
            + "risk_result = client.assess_excavation_risk(\n"
            + f"    project_id=\"{project_id}\",\n"
            + f"    excavation_depth={excavation_depth},\n"
            + f"    construction_method=\"{construction_method}\",\n"
            + "    excavation_area={\"type\": \"Polygon\", \"coordinates\": \"<GeoJSON>\"},\n"
            + f"    entitlement_id=\"{entitlement_id}\",\n"
            + ")\n"
        )

    def source_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        grid_preview = self.power_data["grid"][:4]
        integrated_preview = self.power_data["integrated-energy"][:4]
        pipeline_preview = self.changchun_assets["pipeline_segments"][:4]
        monitoring_preview = [
            {"asset_type": asset_type, **summary}
            for asset_type, summary in self.changchun_assets["monitoring_summary"].items()
        ]
        product_preview = [
            {
                "product_id": product_id,
                "product_version": package["product_manifest"]["product_version"],
                "ontology_version": (
                    package["product_manifest"]["ontology"]["id"]
                    + "@"
                    + package["product_manifest"]["ontology"]["version"]
                ),
                "actions": ", ".join(package["product_manifest"]["actions"]),
                "readable_fields": len(package["product_manifest"]["readable_fields"]),
            }
            for product_id, package in self.products.items()
        ]
        entitlement_preview = [
            {
                "entitlement_id": entitlement.entitlement_id,
                "product_id": entitlement.product_id,
                "provider_id": entitlement.provider_id,
                "purpose": entitlement.purpose,
                "used_calls": entitlement.used_calls,
                "max_calls": entitlement.max_calls,
                "revoked": entitlement.revoked,
            }
            for entitlement in list(self.policy.all().values())[-4:]
        ]
        audit_preview = [
            {
                "event_hash": event["hash"],
                "request_id": event["receipt"]["request_id"],
                "product_version": event["receipt"]["product_version"],
                "output_hash": event["receipt"]["output_hash"],
            }
            for event in self.audit.events()[-4:]
        ]
        grid_rows = [
            {
                "table": "grid.monthly_usage",
                "business_object": "EnergyUsage",
                "fields": "usage_month, total_kwh, unified_credit_code, source_row_id",
                "sample_rows": len(self.power_data["grid"]),
                "osdk_exposure": "kwh=COMPUTE_ONLY, period=INTERNAL_ONLY",
                "preview_rows": [
                    {
                        "unified_credit_code": row["enterprise_id"],
                        "usage_month": row["period"],
                        "total_kwh": row["kwh"],
                        "source_row_id": row["source_row_id"],
                    }
                    for row in grid_preview
                ],
            },
            {
                "table": "grid.payment",
                "business_object": "BillingRecord",
                "fields": "payment_status, late_days, source_row_id",
                "sample_rows": len(self.power_data["grid"]),
                "osdk_exposure": "late_days=AGGREGATE_ONLY",
                "preview_rows": [
                    {
                        "unified_credit_code": row["enterprise_id"],
                        "payment_status": row["payment_status"],
                        "late_days": row["late_days"],
                        "source_row_id": row["source_row_id"],
                    }
                    for row in grid_preview
                ],
            },
        ]
        energy_rows = [
            {
                "table": "integrated_energy.billing",
                "business_object": "EnergyUsage",
                "fields": "period_code, energy_qty, enterprise_no, source_row_id",
                "sample_rows": len(self.power_data["integrated-energy"]),
                "osdk_exposure": "energy_qty maps to EnergyUsage.kwh",
                "preview_rows": [
                    {
                        "enterprise_no": row["enterprise_id"],
                        "period_code": row["period"].replace("-", ""),
                        "energy_qty": row["kwh"],
                        "source_row_id": row["source_row_id"],
                    }
                    for row in integrated_preview
                ],
            },
            {
                "table": "integrated_energy.charge",
                "business_object": "BillingRecord",
                "fields": "settle_status, late_days, source_row_id",
                "sample_rows": len(self.power_data["integrated-energy"]),
                "osdk_exposure": "late_days=AGGREGATE_ONLY",
                "preview_rows": [
                    {
                        "enterprise_no": row["enterprise_id"],
                        "settle_status": row["payment_status"],
                        "late_days": row["late_days"],
                        "source_row_id": row["source_row_id"],
                    }
                    for row in integrated_preview
                ],
            },
        ]
        changchun_rows = [
            {
                "table": "gis.pipeline_layer",
                "business_object": "PipelineSegment",
                "fields": "geometry, asset_type, owner, depth",
                "sample_rows": len(self.changchun_assets["pipeline_segments"]),
                "osdk_exposure": "exact_coordinates=COMPUTE_ONLY after core upgrade",
                "preview_rows": [
                    {
                        "segment_id": row["segment_id"],
                        "asset_type": row["asset_type"],
                        "geometry": row["line"],
                        "depth": row["depth"],
                        "material": row["material"],
                    }
                    for row in pipeline_preview
                ],
            },
            {
                "table": "iot.monitoring_summary",
                "business_object": "MonitoringSignal",
                "fields": "asset_type, alerts_30d, quality",
                "sample_rows": len(self.changchun_assets["monitoring_summary"]),
                "osdk_exposure": "quality_summary=EXTERNAL_RESULT",
                "preview_rows": monitoring_preview,
            },
            {
                "table": "ops.historical_hazards",
                "business_object": "HazardEvent",
                "fields": "asset_type, count, severity",
                "sample_rows": len(self.changchun_assets["historical_hazards"]),
                "osdk_exposure": "used only by local risk action",
                "preview_rows": self.changchun_assets["historical_hazards"],
            },
        ]
        ops_rows = [
            {
                "table": "doir_registry.product_versions",
                "business_object": "ProductProjection",
                "fields": "ontology_version, product_version, actions, outputs",
                "sample_rows": len(self.products),
                "osdk_exposure": "source of generated Product OSDK",
                "preview_rows": product_preview,
            },
            {
                "table": "policy.entitlements",
                "business_object": "Entitlement",
                "fields": "purpose, requester_agent, provider_id, expires_at",
                "sample_rows": len(self.policy.all()),
                "osdk_exposure": "checked before every Runtime action",
                "preview_rows": entitlement_preview,
            },
            {
                "table": "audit.hash_chain_events",
                "business_object": "ExecutionReceipt",
                "fields": "input_hash, output_hash, previous_event_hash, signature",
                "sample_rows": len(self.audit.events()),
                "osdk_exposure": "verifies result provenance",
                "preview_rows": audit_preview,
            },
        ]
        return {
            "power-credit": grid_rows + energy_rows,
            "changchun-risk": changchun_rows,
            "ontology-ops": ops_rows,
        }

    def recompile_coordinate_core(self) -> Dict[str, Any]:
        before = self.products["changchun-excavation-risk"]["product_manifest"]
        self.coordinate_core = True
        self.products["changchun-excavation-risk"] = compile_product(
            "changchun-excavation-risk", coordinate_core=True
        ).model_dump(mode="json")
        after = self.products["changchun-excavation-risk"]["product_manifest"]
        return {
            "result": {
                "operation": "coordinate_core_recompile",
                "coordinate_core": self.coordinate_core,
                "version_before": before["product_version"],
                "version_after": after["product_version"],
                "readable_fields_after": after["readable_fields"],
            },
            "trace": [
                {
                    "title": "接收动态本体运维请求",
                    "actor": "OntologyOps Console",
                    "detail": "运维人员将管线精确坐标升级为核心数据，触发产品影响分析。",
                    "facts": {"field": "PipelineSegment.exact_coordinates"},
                },
                {
                    "title": "更新分类分级策略",
                    "actor": "DOIR Registry",
                    "detail": "exact_coordinates 从 INTERNAL_ONLY 转为 COMPUTE_ONLY，不允许直接出现在 OSDK 读取接口。",
                    "facts": {"new_exposure": "COMPUTE_ONLY"},
                },
                {
                    "title": "重新编译产品投影",
                    "actor": "Product Compiler",
                    "detail": "Compiler 重新裁剪 OSDK 表面，保留 assess_excavation_risk 动作，移除坐标读取面。",
                    "facts": {
                        "version_before": before["product_version"],
                        "version_after": after["product_version"],
                    },
                },
                {
                    "title": "发布新 Product OSDK 合同",
                    "actor": "OSDK Generator",
                    "detail": "Runtime 仍可在数据域内使用坐标计算风险，外部只看到风险摘要。",
                    "facts": {
                        "actions": after["actions"],
                        "readable_fields": [
                            f"{field['object']}.{field['property']}"
                            for field in after["readable_fields"]
                        ],
                    },
                },
            ],
            "product_package": self.products["changchun-excavation-risk"],
        }

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
                "code": self._power_osdk_code(
                    product_package=product_package,
                    enterprise_id=enterprise_id,
                    months=months,
                    entitlement_id=entitlement_id,
                ),
            },
            {
                "title": "OSDK 调用动态本体动作",
                "actor": "Product OSDK + Runtime Binding",
                "detail": "上一段代码把企业 ID、月份和授权编号交给 action_id=compute_credit_features；Runtime Binding 再按本体动作声明解析内部依赖。depends_on 不是外部传参，而是数据域内要读取/计算的本体字段。",
                "facts": {
                    "external_payload": ["enterprise_id", "months", "entitlement_id"],
                    "ontology_action": product_package["runtime_binding"][
                        "internal_dependencies"
                    ]["compute_credit_features"],
                },
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
        product_package = self.products[product_id]
        trace = [
            {
                "title": "前端提交开挖风险请求",
                "actor": "Demo Console",
                "detail": "用户提交工程 ID、开挖深度、施工方式和 GeoJSON 区域，不请求管线坐标。",
                "facts": {
                    "project_id": project_id,
                    "excavation_depth": excavation_depth,
                    "construction_method": construction_method,
                },
            },
            {
                "title": "应用获得 Product OSDK 调用面",
                "actor": "Generated OSDK",
                "detail": "OSDK 只暴露 assess_excavation_risk 动作和风险摘要输出。",
                "code": self._changchun_osdk_code(
                    product_package=product_package,
                    project_id=project_id,
                    excavation_depth=excavation_depth,
                    construction_method=construction_method,
                    entitlement_id=entitlement_id,
                ),
            },
            {
                "title": "OSDK 调用动态本体动作",
                "actor": "Product OSDK + Runtime Binding",
                "detail": "上一段代码只提交工程参数、区域和授权编号；Runtime Binding 再按本体动作声明解析 PipelineSegment 与 ExcavationProject 的内部依赖。depends_on 不是外部传参，而是数据域内计算风险需要用到的本体字段。",
                "facts": {
                    "external_payload": [
                        "project_id",
                        "excavation_area",
                        "excavation_depth",
                        "construction_method",
                        "entitlement_id",
                    ],
                    "ontology_action": product_package["runtime_binding"][
                        "internal_dependencies"
                    ]["assess_excavation_risk"],
                },
            },
            {
                "title": "Runtime 将本体映射到 GIS/IoT 底层表",
                "actor": "长春城市生命线 Provider Runtime",
                "detail": "精确坐标和监测摘要只在数据域内用于空间计算，不返回给请求方。",
                "facts": {
                    "PipelineSegment.exact_coordinates": "gis.pipeline_layer.geometry",
                    "PipelineSegment.asset_type": "gis.pipeline_layer.asset_type",
                    "MonitoringSignal.summary": "iot.monitoring_summary",
                },
            },
            {
                "title": "本地空间规则计算风险",
                "actor": "Provider Runtime",
                "detail": "Runtime 对开挖范围做 bbox-buffer 相交判断，并结合深度、施工方式和资产权重评分。",
                "facts": {
                    "pipeline_segments_scanned": len(
                        self.changchun_assets["pipeline_segments"]
                    ),
                    "affected_segment_count": len(affected),
                    "risk_score": round(risk_score, 3),
                },
            },
            {
                "title": "输出过滤为风险摘要",
                "actor": "Output Filter",
                "detail": "只返回风险等级、影响资产类型、段数和建议，不返回坐标、拓扑或业主明细。",
                "facts": {
                    "returned_fields": list(result.keys()),
                    "blocked_fields": [
                        "exact_coordinates",
                        "segment_id",
                        "owner_detail",
                        "raw_monitoring_series",
                    ],
                },
            },
        ]
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

    def run_changchun_demo(
        self,
        *,
        project_id: str = "CC-2026-001",
        excavation_depth: float = 3.5,
        construction_method: str = "MECHANICAL",
    ) -> Dict[str, Any]:
        product_id = "changchun-excavation-risk"
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
            excavation_depth=excavation_depth,
            construction_method=construction_method,
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
