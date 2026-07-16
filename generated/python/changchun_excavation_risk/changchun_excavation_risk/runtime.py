from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .errors import (
    ContractViolation,
    EntitlementExpired,
    PolicyDenied,
    ProviderRuntimeClientError,
    RuntimeUnavailable,
)


class ProviderRuntimeClient:
    """Remote client for Product OSDK workloads.

    The generated Product OSDK never receives a database handle or an
    internal Runtime object. It sends a signed/identified product action
    envelope to a trusted gateway, and the gateway routes to Provider
    Runtime after policy checks.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        requester_agent: str,
        timeout: float = 20,
        default_purpose: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.requester_agent = requester_agent
        self.timeout = timeout
        self.default_purpose = default_purpose

    def execute_action(
        self,
        *,
        product_id: str,
        action_id: str,
        provider_id: str,
        entitlement_id: str,
        payload: Dict[str, Any],
        purpose: str,
        product_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        envelope = {
            "request_id": f"req_{uuid4().hex[:12]}",
            "requester_agent": self.requester_agent,
            "provider_id": provider_id,
            "product_id": product_id,
            "product_version": product_version,
            "action_id": action_id,
            "entitlement_id": entitlement_id,
            "purpose": purpose or self.default_purpose,
            "payload": payload,
            "client_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self._post("/actions/execute", envelope)

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = _read_error_detail(exc)
            _raise_for_gateway_error(exc.code, detail)
        except URLError as exc:
            raise RuntimeUnavailable(str(exc)) from exc
        _raise_for_gateway_error(200, payload)
        return payload


class AsyncProviderRuntimeClient:
    def __init__(self, **kwargs: Any) -> None:
        self._sync = ProviderRuntimeClient(**kwargs)

    async def execute_action(self, **kwargs: Any) -> Dict[str, Any]:
        return await asyncio.to_thread(self._sync.execute_action, **kwargs)


def _read_error_detail(exc: HTTPError) -> Any:
    try:
        return json.loads(exc.read().decode("utf-8"))
    except Exception:
        return {"detail": str(exc)}


def _raise_for_gateway_error(status_code: int, payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    status = payload.get("status")
    detail = payload.get("detail", payload)
    reason = payload.get("error_code") or payload.get("reason")
    if isinstance(detail, dict):
        reason = reason or detail.get("error_code") or detail.get("reason")
        status = status or detail.get("status")
    if status == "denied" or status_code in {401, 403}:
        if reason == "entitlement_expired":
            raise EntitlementExpired("entitlement expired", status_code=status_code, detail=detail)
        raise PolicyDenied(str(reason or "policy denied"), status_code=status_code, detail=detail)
    if status == "contract_error" or status_code == 422:
        raise ContractViolation(str(reason or "contract violation"), status_code=status_code, detail=detail)
    if status_code >= 500:
        raise RuntimeUnavailable(str(reason or "runtime unavailable"), status_code=status_code, detail=detail)
    if status == "failed":
        raise ProviderRuntimeClientError(str(reason or "runtime failed"), status_code=status_code, detail=detail)
