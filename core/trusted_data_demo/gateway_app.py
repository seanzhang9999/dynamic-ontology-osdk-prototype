from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .audit import AuditLog
from .control_plane import GatewayControlPlane
from .gateway import GatewayError, HttpProviderTransport, ProviderTransport, SimpleTrustedGateway


DEFAULT_PROVIDER_ROUTES = {
    "grid": "http://127.0.0.1:8010",
    "integrated-energy": "http://127.0.0.1:8011",
    "changchun": "http://127.0.0.1:8012",
}


def provider_routes_from_env() -> Dict[str, str]:
    raw = os.getenv("PROVIDER_RUNTIME_ROUTES")
    if not raw:
        return dict(DEFAULT_PROVIDER_ROUTES)
    routes = json.loads(raw)
    if not isinstance(routes, dict) or not routes:
        raise ValueError("PROVIDER_RUNTIME_ROUTES must be a non-empty JSON object")
    return {str(key): str(value) for key, value in routes.items()}


def create_gateway_app(
    *,
    control_plane: Optional[GatewayControlPlane] = None,
    provider_transport: Optional[ProviderTransport] = None,
):
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    control = control_plane or GatewayControlPlane()
    routes = provider_routes_from_env()
    transport = provider_transport or HttpProviderTransport(
        routes,
        internal_key=os.getenv(
            "GATEWAY_PROVIDER_INTERNAL_KEY", "demo_gateway_provider_key"
        ),
        timeout=float(os.getenv("PROVIDER_RUNTIME_TIMEOUT_SECONDS", "10")),
    )
    gateway = SimpleTrustedGateway(control, provider_transport=transport)
    app = FastAPI(title="Trusted Product Gateway", version="0.2.0")
    app.state.control_plane = control
    app.state.gateway = gateway
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "gateway",
            "provider_ids": sorted(routes),
        }

    @app.get("/products")
    def products() -> Dict[str, Any]:
        return gateway.products()

    @app.get("/products/{product_id}")
    def product(product_id: str) -> Dict[str, Any]:
        try:
            return control.products[product_id]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="product_not_found") from exc

    @app.post("/entitlements")
    def create_entitlement(payload: Dict[str, Any]) -> Dict[str, Any]:
        product_id = payload["product_id"]
        default_requester = (
            "agent:construction-safety"
            if product_id == "changchun-excavation-risk"
            else "agent:bank-risk"
        )
        try:
            return control.create_entitlement(
                product_id=product_id,
                provider_id=payload["provider_id"],
                data_subject=payload["data_subject"],
                requester_agent=payload.get("requester_agent", default_requester),
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/entitlements/{entitlement_id}/revoke")
    def revoke_entitlement(entitlement_id: str) -> Dict[str, Any]:
        return control.revoke_entitlement(entitlement_id)

    @app.post("/actions/execute")
    def execute_action(
        payload: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            response = gateway.execute_action(payload, api_key=x_api_key)
        except GatewayError as exc:
            status_code = 403 if exc.status == "denied" else 422
            raise HTTPException(
                status_code=status_code,
                detail={"status": exc.status, "error_code": exc.reason},
            ) from exc
        if response["status"] == "denied":
            raise HTTPException(status_code=403, detail=response)
        return response

    @app.post("/receipts/verify")
    def verify_receipt(payload: Dict[str, Any]) -> Dict[str, bool]:
        return {"valid": AuditLog.verify(payload)}

    @app.post("/demo/run/remote-power-credit")
    def run_remote_power_credit(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        enterprise_id = payload.get("enterprise_id", "91300000DEMO0007")
        provider_ids = payload.get(
            "provider_ids", ["grid", "integrated-energy"]
        )
        bindings = []
        for provider_id in provider_ids:
            entitlement = control.create_entitlement(
                product_id="enterprise-energy-credit",
                provider_id=provider_id,
                data_subject=enterprise_id,
                requester_agent="agent:bank-risk",
            )
            bindings.append(
                {
                    "provider_id": provider_id,
                    "entitlement_id": entitlement["entitlement_id"],
                }
            )
        product_manifest = control.products["enterprise-energy-credit"]["product_manifest"]
        envelope = {
            "request_id": "req_demo_remote_fanout",
            "requester_agent": "agent:bank-risk",
            "product_id": "enterprise-energy-credit",
            "product_version": product_manifest["product_version"],
            "action_id": "compute_credit_features",
            "providers": bindings,
            "purpose": product_manifest["purpose"],
            "payload": {
                "enterprise_id": enterprise_id,
                "months": int(payload.get("months", 12)),
            },
        }
        return gateway.execute_action(envelope, api_key="demo_key_bank_agent")

    return app


app = create_gateway_app()
