from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .audit import sha256_json
from .models import PolicyDecision


class GatewayError(ValueError):
    def __init__(self, reason: str, *, status: str = "contract_error") -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


class ProviderTransportError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ProviderTransport(Protocol):
    def execute(self, provider_id: str, envelope: Dict[str, Any]) -> Dict[str, Any]: ...


class InProcessProviderTransport:
    """Compatibility transport for the original all-in-one demo."""

    def __init__(self, demo: Any) -> None:
        self.demo = demo

    def execute(self, provider_id: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
        decision = PolicyDecision.model_validate(envelope["policy_decision"])
        job = self.demo.execute_product_action(
            product_id=envelope["product_id"],
            action_id=envelope["action_id"],
            provider_id=provider_id,
            entitlement_id=envelope["entitlement_id"],
            payload=envelope["payload"],
            requester_agent=envelope["requester_agent"],
            policy_decision=decision,
        )
        return job.model_dump(mode="json")


class HttpProviderTransport:
    """Private Gateway-to-Provider Runtime HTTP transport."""

    def __init__(
        self,
        routes: Dict[str, str],
        *,
        internal_key: str,
        timeout: float = 10,
    ) -> None:
        self.routes = {key: value.rstrip("/") for key, value in routes.items()}
        self.internal_key = internal_key
        self.timeout = timeout

    def execute(self, provider_id: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
        try:
            base_url = self.routes[provider_id]
        except KeyError as exc:
            raise ProviderTransportError("provider_not_registered") from exc
        request = Request(
            base_url + "/internal/actions/execute",
            data=json.dumps(envelope).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Gateway-Key": self.internal_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except Exception:
                detail = {}
            reason = _nested_reason(detail) or f"provider_http_{exc.code}"
            raise ProviderTransportError(reason) from exc
        except (TimeoutError, URLError) as exc:
            raise ProviderTransportError("provider_unavailable") from exc


class SimpleTrustedGateway:
    """Trusted product Gateway with single-request multi-provider fan-out."""

    def __init__(
        self,
        control_plane: Any,
        *,
        provider_transport: Optional[ProviderTransport] = None,
        max_workers: int = 8,
    ) -> None:
        self.control_plane = control_plane
        self.provider_transport = provider_transport or InProcessProviderTransport(control_plane)
        self.max_workers = max_workers
        self.api_keys = {
            "demo_key_bank_agent": "agent:bank-risk",
            "demo_key_construction_agent": "agent:construction-safety",
        }

    @property
    def demo(self) -> Any:
        return self.control_plane

    def products(self) -> Dict[str, Any]:
        return {
            product_id: package["product_manifest"]
            for product_id, package in self.control_plane.products.items()
        }

    def execute_action(
        self,
        envelope: Dict[str, Any],
        *,
        api_key: Optional[str],
    ) -> Dict[str, Any]:
        trace: List[Dict[str, Any]] = []
        requester_agent = self._authenticate(api_key, envelope, trace)
        product_id = self._required(envelope, "product_id")
        action_id = self._required(envelope, "action_id")
        payload = envelope.get("payload") or {}
        product_package = self._product_contract(product_id, action_id, envelope, trace)
        bindings, is_fanout = self._provider_bindings(envelope)
        self._validate_provider_bindings(product_id, bindings)

        preflight: Dict[str, Dict[str, Any]] = {}
        dispatchable: List[Dict[str, str]] = []
        for binding in bindings:
            provider_id = binding["provider_id"]
            entitlement_id = binding["entitlement_id"]
            self._validate_action_payload(
                product_package,
                action_id,
                payload,
                provider_id,
                entitlement_id,
                trace,
            )
            decision = self._evaluate_entitlement(
                product_package,
                product_id,
                requester_agent,
                provider_id,
                entitlement_id,
                consume=False,
            )
            if decision.allowed:
                dispatchable.append(binding)
            else:
                preflight[provider_id] = self._provider_denied(provider_id, decision.reason)

        trace.append(
            {
                "title": "Gateway 校验 Provider Entitlements",
                "actor": "Simple Trusted Gateway",
                "detail": "网关逐 Provider 校验授权；被拒绝的 Provider 不会收到 Runtime 请求。",
                "facts": {
                    "requested_providers": [item["provider_id"] for item in bindings],
                    "dispatchable_providers": [item["provider_id"] for item in dispatchable],
                },
            }
        )

        dispatched = self._dispatch(
            envelope=envelope,
            product_package=product_package,
            requester_agent=requester_agent,
            bindings=dispatchable,
            payload=payload,
        )
        provider_results = {
            binding["provider_id"]: (
                dispatched.get(binding["provider_id"])
                or preflight[binding["provider_id"]]
            )
            for binding in bindings
        }

        if not is_fanout:
            only = provider_results[bindings[0]["provider_id"]]
            return self._legacy_response(envelope, trace, only)
        return self._fanout_response(envelope, trace, provider_results)

    def _dispatch(
        self,
        *,
        envelope: Dict[str, Any],
        product_package: Dict[str, Any],
        requester_agent: str,
        bindings: List[Dict[str, str]],
        payload: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        if not bindings:
            return {}
        product_id = envelope["product_id"]
        action_id = envelope["action_id"]
        calls: Dict[str, Dict[str, Any]] = {}
        for binding in bindings:
            provider_id = binding["provider_id"]
            entitlement_id = binding["entitlement_id"]
            decision = self._evaluate_entitlement(
                product_package,
                product_id,
                requester_agent,
                provider_id,
                entitlement_id,
                consume=True,
            )
            if not decision.allowed:
                calls[provider_id] = self._provider_denied(provider_id, decision.reason)
                continue
            calls[provider_id] = {
                "request_id": envelope.get("request_id"),
                "requester_agent": requester_agent,
                "provider_id": provider_id,
                "product_id": product_id,
                "product_version": product_package["product_manifest"]["product_version"],
                "action_id": action_id,
                "entitlement_id": entitlement_id,
                "purpose": product_package["product_manifest"]["purpose"],
                "payload": payload,
                "policy_decision": decision.model_dump(mode="json"),
            }

        results: Dict[str, Dict[str, Any]] = {
            provider_id: call
            for provider_id, call in calls.items()
            if call.get("status") == "denied"
        }
        outbound = {
            provider_id: call
            for provider_id, call in calls.items()
            if call.get("status") != "denied"
        }
        worker_count = min(self.max_workers, len(outbound))
        if not worker_count:
            return results
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(self.provider_transport.execute, provider_id, call): provider_id
                for provider_id, call in outbound.items()
            }
            for future in as_completed(futures):
                provider_id = futures[future]
                try:
                    results[provider_id] = self._provider_success(
                        provider_id, future.result()
                    )
                except ProviderTransportError as exc:
                    results[provider_id] = self._provider_failed(provider_id, exc.reason)
                except Exception:
                    results[provider_id] = self._provider_failed(
                        provider_id, "provider_transport_error"
                    )
        return results

    def _evaluate_entitlement(
        self,
        product_package: Dict[str, Any],
        product_id: str,
        requester_agent: str,
        provider_id: str,
        entitlement_id: str,
        *,
        consume: bool,
    ) -> PolicyDecision:
        manifest = product_package["product_manifest"]
        return self.control_plane.policy.evaluate(
            entitlement_id=entitlement_id,
            product_id=product_id,
            purpose=manifest["purpose"],
            requester_agent=requester_agent,
            provider_id=provider_id,
            output_granularity=manifest["output_granularity"],
            consume=consume,
        )

    def _provider_bindings(
        self, envelope: Dict[str, Any]
    ) -> tuple[List[Dict[str, str]], bool]:
        raw_bindings = envelope.get("providers")
        is_fanout = raw_bindings is not None
        if raw_bindings is None:
            raw_bindings = [
                {
                    "provider_id": self._required(envelope, "provider_id"),
                    "entitlement_id": self._required(envelope, "entitlement_id"),
                }
            ]
        if not isinstance(raw_bindings, list) or not raw_bindings:
            raise GatewayError("providers_must_be_non_empty_list")
        bindings: List[Dict[str, str]] = []
        seen = set()
        for raw in raw_bindings:
            if not isinstance(raw, dict):
                raise GatewayError("invalid_provider_binding")
            provider_id = self._required(raw, "provider_id")
            entitlement_id = self._required(raw, "entitlement_id")
            if provider_id in seen:
                raise GatewayError(f"duplicate_provider_id:{provider_id}")
            seen.add(provider_id)
            bindings.append(
                {"provider_id": str(provider_id), "entitlement_id": str(entitlement_id)}
            )
        return bindings, is_fanout

    def _validate_provider_bindings(
        self, product_id: str, bindings: List[Dict[str, str]]
    ) -> None:
        mappings = self.control_plane.registry.list_provider_mappings()
        for binding in bindings:
            provider_id = binding["provider_id"]
            mapping = mappings.get(provider_id)
            if mapping is None:
                raise GatewayError(f"provider_not_registered:{provider_id}")
            if mapping["product_id"] != product_id:
                raise GatewayError(f"provider_not_available_for_product:{provider_id}")

    def _authenticate(
        self, api_key: Optional[str], envelope: Dict[str, Any], trace: List[Dict[str, Any]]
    ) -> str:
        if not api_key or api_key not in self.api_keys:
            raise GatewayError("invalid_api_key", status="denied")
        requester_agent = envelope.get("requester_agent") or self.api_keys[api_key]
        if requester_agent != self.api_keys[api_key]:
            raise GatewayError("requester_api_key_mismatch", status="denied")
        trace.append(
            {
                "title": "Gateway 校验远程 OSDK 身份",
                "actor": "Simple Trusted Gateway",
                "detail": "远程 OSDK 使用 API key 证明 workload 身份。",
                "facts": {"requester_agent": requester_agent},
            }
        )
        return requester_agent

    def _product_contract(
        self,
        product_id: str,
        action_id: str,
        envelope: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        try:
            package = self.control_plane.products[product_id]
        except KeyError as exc:
            raise GatewayError("product_not_found") from exc
        manifest = package["product_manifest"]
        if action_id not in manifest["actions"]:
            raise GatewayError("action_not_in_product_contract")
        requested_version = envelope.get("product_version")
        if requested_version and requested_version != manifest["product_version"]:
            raise GatewayError("product_version_mismatch")
        trace.append(
            {
                "title": "Gateway 校验产品契约",
                "actor": "Simple Trusted Gateway",
                "detail": "网关确认 product/action/version 已发布。",
                "facts": {
                    "product_version": manifest["product_version"],
                    "actions": manifest["actions"],
                },
            }
        )
        return package

    def _validate_action_payload(
        self,
        product_package: Dict[str, Any],
        action_id: str,
        payload: Dict[str, Any],
        provider_id: str,
        entitlement_id: str,
        trace: List[Dict[str, Any]],
    ) -> None:
        action = product_package["action_schemas"][action_id]
        inputs = action.get("inputs", {})
        combined = {
            **payload,
            "provider_id": provider_id,
            "entitlement_id": entitlement_id,
        }
        missing = [
            name
            for name, spec in inputs.items()
            if spec.get("required", True)
            and "default" not in spec
            and combined.get(name) is None
        ]
        if missing:
            raise GatewayError(f"missing_action_inputs:{','.join(missing)}")
        allowed_payload = {
            name for name, spec in inputs.items() if spec.get("transport") != "envelope"
        }
        unknown = sorted(set(payload.keys()) - allowed_payload)
        if unknown:
            raise GatewayError(f"unknown_payload_fields:{','.join(unknown)}")
        if not any(step.get("title") == "Gateway 校验 action 参数" for step in trace):
            trace.append(
                {
                    "title": "Gateway 校验 action 参数",
                    "actor": "Simple Trusted Gateway",
                    "detail": "网关使用 DOIR action input schema 校验共享业务 payload。",
                    "facts": {
                        "action_id": action_id,
                        "payload_fields": sorted(payload.keys()),
                        "internal_dependencies": action.get("depends_on", []),
                    },
                }
            )

    def _legacy_response(
        self,
        envelope: Dict[str, Any],
        trace: List[Dict[str, Any]],
        provider_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        if provider_result["status"] == "denied":
            return self._denied(envelope, trace, provider_result["error_code"])
        if provider_result["status"] == "failed":
            return {
                "request_id": envelope.get("request_id"),
                "status": "failed",
                "reason": provider_result["error_code"],
                "error_code": provider_result["error_code"],
                "result": None,
                "receipt_id": None,
                "trace": trace,
            }
        return {
            "request_id": envelope.get("request_id") or provider_result.get("job_id"),
            "status": "succeeded",
            "result": provider_result.get("result"),
            "receipt_id": provider_result.get("receipt_id"),
            "policy_decision": provider_result.get("policy_decision"),
            "runtime_version": provider_result.get("runtime_version"),
            "job_id": provider_result.get("job_id"),
            "gateway": {
                "input_hash": sha256_json(envelope),
                "output_hash": sha256_json(provider_result.get("result") or {}),
            },
            "trace": trace,
            "runtime_trace": provider_result.get("runtime_trace", []),
            "receipt": provider_result.get("receipt"),
        }

    def _fanout_response(
        self,
        envelope: Dict[str, Any],
        trace: List[Dict[str, Any]],
        provider_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        statuses = [item["status"] for item in provider_results.values()]
        succeeded = sum(status == "succeeded" for status in statuses)
        if succeeded == len(statuses):
            status = "completed"
        elif succeeded:
            status = "partial"
        else:
            status = "failed"
        trace.append(
            {
                "title": "Gateway 汇集 Provider 响应",
                "actor": "Simple Trusted Gateway",
                "detail": "Gateway 不执行银行评分，只关联每个 Provider 的受控结果与 Receipt。",
                "facts": {
                    "status": status,
                    "provider_statuses": {
                        key: value["status"] for key, value in provider_results.items()
                    },
                },
            }
        )
        return {
            "request_id": envelope.get("request_id"),
            "status": status,
            "product_id": envelope["product_id"],
            "action_id": envelope["action_id"],
            "provider_results": provider_results,
            "gateway": {
                "input_hash": sha256_json(envelope),
                "output_hash": sha256_json(provider_results),
            },
            "trace": trace,
        }

    @staticmethod
    def _provider_success(provider_id: str, job: Dict[str, Any]) -> Dict[str, Any]:
        job_status = job.get("status")
        if job_status == "denied":
            decision = job.get("policy_decision") or {}
            reason = decision.get("reason") if isinstance(decision, dict) else "provider_denied"
            return SimpleTrustedGateway._provider_denied(provider_id, reason)
        if job_status != "success":
            return SimpleTrustedGateway._provider_failed(provider_id, "provider_execution_failed")
        receipt = job.get("receipt")
        return {
            "provider_id": provider_id,
            "status": "succeeded",
            "result": job.get("result"),
            "error_code": None,
            "receipt_id": receipt.get("request_id") if isinstance(receipt, dict) else None,
            "runtime_version": receipt.get("runtime_version") if isinstance(receipt, dict) else None,
            "job_id": job.get("job_id"),
            "policy_decision": (job.get("policy_decision") or {}).get("reason"),
            "runtime_trace": job.get("trace", []),
            "receipt": receipt,
        }

    @staticmethod
    def _provider_denied(provider_id: str, reason: str) -> Dict[str, Any]:
        return {
            "provider_id": provider_id,
            "status": "denied",
            "result": None,
            "error_code": reason,
            "receipt_id": None,
            "runtime_version": None,
            "job_id": None,
            "policy_decision": reason,
            "runtime_trace": [],
            "receipt": None,
        }

    @staticmethod
    def _provider_failed(provider_id: str, reason: str) -> Dict[str, Any]:
        result = SimpleTrustedGateway._provider_denied(provider_id, reason)
        result["status"] = "failed"
        return result

    def _denied(
        self,
        envelope: Dict[str, Any],
        trace: List[Dict[str, Any]],
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "request_id": envelope.get("request_id"),
            "status": "denied",
            "reason": reason,
            "error_code": reason,
            "result": None,
            "receipt_id": None,
            "policy_decision": reason,
            "job_id": None,
            "trace": trace,
        }

    @staticmethod
    def _required(envelope: Dict[str, Any], key: str) -> Any:
        value = envelope.get(key)
        if value in (None, ""):
            raise GatewayError(f"missing_{key}")
        return value


def _nested_reason(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    reason = payload.get("error_code") or payload.get("reason")
    detail = payload.get("detail")
    if not reason and isinstance(detail, dict):
        reason = detail.get("error_code") or detail.get("reason")
    return str(reason) if reason else None
