from __future__ import annotations

from typing import Any, Dict, Optional

from .audit import AuditLog
from .models import ApplicationManifest
from .runtime import DEFAULT_APP, TrustedDataDemo


demo = TrustedDataDemo()


def create_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="Trusted Data Product Flow Demo", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/demo/state")
    def state() -> Dict[str, Any]:
        return demo.state()

    @app.get("/products/{product_id}")
    def product(product_id: str) -> Dict[str, Any]:
        try:
            return demo.products[product_id]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="product_not_found") from exc

    @app.post("/entitlements")
    def create_entitlement(payload: Dict[str, Any]) -> Dict[str, Any]:
        return demo.create_entitlement(
            product_id=payload["product_id"],
            provider_id=payload["provider_id"],
            data_subject=payload["data_subject"],
            requester_agent=payload.get("requester_agent", DEFAULT_APP.requester_agent),
        )

    @app.post("/entitlements/verify")
    def verify_entitlement(payload: Dict[str, Any]) -> Dict[str, Any]:
        decision = demo.policy.evaluate(
            entitlement_id=payload["entitlement_id"],
            product_id=payload["product_id"],
            purpose=payload["purpose"],
            requester_agent=payload["requester_agent"],
            provider_id=payload["provider_id"],
            output_granularity=payload["output_granularity"],
        )
        return decision.model_dump(mode="json")

    @app.post("/entitlements/{entitlement_id}/revoke")
    def revoke_entitlement(entitlement_id: str) -> Dict[str, Any]:
        return demo.revoke_entitlement(entitlement_id)

    @app.post("/policy/evaluate")
    def policy_evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
        decision = demo.policy.evaluate(**payload)
        return decision.model_dump(mode="json")

    @app.post("/applications/submit")
    def submit_application(payload: Dict[str, Any]) -> Dict[str, Any]:
        manifest = ApplicationManifest.model_validate(payload)
        return {
            "accepted": True,
            "application_digest": manifest.digest,
            "allowed_products": manifest.allowed_products,
        }

    @app.post("/jobs/execute")
    def execute_job(payload: Dict[str, Any]) -> Dict[str, Any]:
        product_id = payload["product_id"]
        if product_id == "enterprise-energy-credit":
            job = demo.execute_power_credit(
                provider_id=payload["provider_id"],
                enterprise_id=payload["enterprise_id"],
                entitlement_id=payload["entitlement_id"],
                months=payload.get("months", 12),
            )
        elif product_id == "changchun-excavation-risk":
            job = demo.execute_changchun_risk(
                entitlement_id=payload["entitlement_id"],
                excavation_area=payload["excavation_area"],
                excavation_depth=payload["excavation_depth"],
                construction_method=payload["construction_method"],
                project_id=payload["project_id"],
            )
        else:
            raise HTTPException(status_code=404, detail="product_not_found")
        return job.model_dump(mode="json")

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> Dict[str, Any]:
        try:
            return demo.get_job(job_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job_not_found") from exc

    @app.get("/receipts/{job_id}")
    def get_receipt(job_id: str) -> Dict[str, Any]:
        try:
            return demo.get_receipt(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="receipt_not_found") from exc

    @app.post("/receipts/verify")
    def verify_receipt(payload: Dict[str, Any]) -> Dict[str, bool]:
        return {"valid": AuditLog.verify(payload)}

    @app.post("/demo/run/power-credit")
    def run_power_credit(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        enterprise_id = (payload or {}).get("enterprise_id", "91300000DEMO0007")
        return demo.run_power_credit_demo(enterprise_id=enterprise_id)

    @app.post("/demo/run/changchun")
    def run_changchun(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        return demo.run_changchun_demo(
            project_id=payload.get("project_id", "CC-2026-001"),
            excavation_depth=float(payload.get("excavation_depth", 3.5)),
            construction_method=payload.get("construction_method", "MECHANICAL"),
        )

    @app.post("/demo/recompile-coordinate-core")
    def recompile_coordinate_core() -> Dict[str, Any]:
        return demo.recompile_coordinate_core()

    return app


app = create_app()
