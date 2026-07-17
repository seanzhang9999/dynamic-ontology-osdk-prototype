from __future__ import annotations

import hmac
import os
from typing import Any, Dict, Optional

from pydantic import ValidationError

from .models import PolicyDecision
from .runtime import TrustedDataDemo


class ProviderRuntimeError(ValueError):
    def __init__(self, reason: str, *, status_code: int = 422) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


class ProviderRuntimeService:
    """Single-provider execution boundary called only by the trusted Gateway."""

    def __init__(
        self,
        *,
        provider_id: str,
        internal_key: str,
        runtime: Optional[TrustedDataDemo] = None,
    ) -> None:
        if not internal_key:
            raise ValueError("internal_gateway_key_required")
        self.provider_id = provider_id
        self.internal_key = internal_key
        self.runtime = runtime or TrustedDataDemo(provider_scope=provider_id)

    def execute(
        self,
        envelope: Dict[str, Any],
        *,
        gateway_key: Optional[str],
    ) -> Dict[str, Any]:
        if not gateway_key or not hmac.compare_digest(gateway_key, self.internal_key):
            raise ProviderRuntimeError("invalid_gateway_key", status_code=403)
        provider_id = _required(envelope, "provider_id")
        if provider_id != self.provider_id:
            raise ProviderRuntimeError("provider_scope_mismatch")
        product_id = _required(envelope, "product_id")
        action_id = _required(envelope, "action_id")
        entitlement_id = _required(envelope, "entitlement_id")
        requester_agent = _required(envelope, "requester_agent")
        try:
            package = self.runtime.products[product_id]
        except KeyError as exc:
            raise ProviderRuntimeError("product_not_found") from exc
        manifest = package["product_manifest"]
        if action_id not in manifest["actions"]:
            raise ProviderRuntimeError("action_not_in_product_contract")
        if envelope.get("product_version") != manifest["product_version"]:
            raise ProviderRuntimeError("product_version_mismatch")
        if envelope.get("purpose") != manifest["purpose"]:
            raise ProviderRuntimeError("purpose_mismatch")
        try:
            decision = PolicyDecision.model_validate(
                envelope.get("policy_decision") or {}
            )
        except ValidationError as exc:
            raise ProviderRuntimeError("invalid_policy_decision") from exc
        if not decision.allowed:
            raise ProviderRuntimeError("gateway_policy_not_allowed", status_code=403)
        if decision.entitlement_id != entitlement_id:
            raise ProviderRuntimeError("policy_entitlement_mismatch", status_code=403)
        job = self.runtime.execute_product_action(
            product_id=product_id,
            action_id=action_id,
            provider_id=provider_id,
            entitlement_id=entitlement_id,
            payload=envelope.get("payload") or {},
            requester_agent=requester_agent,
            policy_decision=decision,
        )
        return job.model_dump(mode="json")


def create_provider_app(
    *,
    provider_id: Optional[str] = None,
    internal_key: Optional[str] = None,
):
    from fastapi import FastAPI, Header, HTTPException

    configured_provider = provider_id or os.getenv("DEMO_PROVIDER_ID", "grid")
    configured_key = internal_key or os.getenv(
        "GATEWAY_PROVIDER_INTERNAL_KEY", "demo_gateway_provider_key"
    )
    service = ProviderRuntimeService(
        provider_id=configured_provider,
        internal_key=configured_key,
    )
    app = FastAPI(
        title=f"{configured_provider} Provider Runtime",
        version="0.2.0",
    )
    app.state.provider_runtime_service = service

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "provider_id": configured_provider}

    @app.post("/internal/actions/execute")
    def execute_action(
        payload: Dict[str, Any],
        x_gateway_key: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            return service.execute(payload, gateway_key=x_gateway_key)
        except ProviderRuntimeError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"status": "denied", "error_code": exc.reason},
            ) from exc

    return app


def _required(payload: Dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value in (None, ""):
        raise ProviderRuntimeError(f"missing_{key}")
    return value


app = create_provider_app()
