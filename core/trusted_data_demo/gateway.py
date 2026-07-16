from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .audit import sha256_json
from .models import ExecutionJob
from .runtime import TrustedDataDemo


class GatewayError(ValueError):
    def __init__(self, reason: str, *, status: str = "contract_error") -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


class SimpleTrustedGateway:
    """Minimal trusted gateway for remote Product OSDK workloads.

    This is deliberately not a production zero-trust gateway. It is the v0.2
    proof that a generated OSDK can run outside the Provider Runtime and still
    be forced through a policy, contract, route, and audit boundary.
    """

    def __init__(self, demo: TrustedDataDemo) -> None:
        self.demo = demo
        self.api_keys = {
            "demo_key_bank_agent": "agent:bank-risk",
            "demo_key_construction_agent": "agent:construction-safety",
        }

    def products(self) -> Dict[str, Any]:
        return {
            product_id: package["product_manifest"]
            for product_id, package in self.demo.products.items()
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
        provider_id = self._required(envelope, "provider_id")
        entitlement_id = self._required(envelope, "entitlement_id")
        payload = envelope.get("payload") or {}
        product_package = self._product_contract(product_id, action_id, envelope, trace)
        self._validate_action_payload(product_package, action_id, envelope, payload, trace)
        decision = self.demo.policy.evaluate(
            entitlement_id=entitlement_id,
            product_id=product_id,
            purpose=product_package["product_manifest"]["purpose"],
            requester_agent=requester_agent,
            provider_id=provider_id,
            output_granularity=product_package["product_manifest"]["output_granularity"],
            consume=False,
        )
        trace.append(
            {
                "title": "Gateway 校验 entitlement",
                "actor": "Simple Trusted Gateway",
                "detail": "网关先做授权 preflight，不消耗调用配额；Runtime 真正执行时再消费配额。",
                "facts": decision.model_dump(mode="json"),
            }
        )
        if not decision.allowed:
            return self._denied(envelope, trace, decision.reason)
        trace.append(
            {
                "title": "Gateway 路由到 Provider Runtime",
                "actor": "Simple Trusted Gateway",
                "detail": "根据 provider_id 将产品动作请求转发到对应 Provider Runtime。",
                "facts": {
                    "provider_id": provider_id,
                    "product_id": product_id,
                    "action_id": action_id,
                },
            }
        )
        job = self.demo.execute_product_action(
            product_id=product_id,
            action_id=action_id,
            provider_id=provider_id,
            entitlement_id=entitlement_id,
            payload=payload,
            requester_agent=requester_agent,
        )
        if not job.policy_decision.allowed:
            return self._denied(envelope, trace + job.trace, job.policy_decision.reason, job=job)
        response = self._success_response(envelope, trace, job)
        return response

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
                "detail": "远程 OSDK 使用 API key 证明 workload 身份；v0.2 用 demo key，生产可替换为签名和 mTLS。",
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
            package = self.demo.products[product_id]
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
                "detail": "网关确认 product/action/version 已发布，远程 OSDK 不能调用未发布动作。",
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
        envelope: Dict[str, Any],
        payload: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> None:
        action = product_package["action_schemas"][action_id]
        inputs = action.get("inputs", {})
        combined = {
            **payload,
            "provider_id": envelope.get("provider_id"),
            "entitlement_id": envelope.get("entitlement_id"),
        }
        missing = [
            name
            for name, spec in inputs.items()
            if spec.get("required", True) and "default" not in spec and combined.get(name) is None
        ]
        if missing:
            raise GatewayError(f"missing_action_inputs:{','.join(missing)}")
        allowed_payload = {
            name for name, spec in inputs.items() if spec.get("transport") != "envelope"
        }
        unknown = sorted(set(payload.keys()) - allowed_payload)
        if unknown:
            raise GatewayError(f"unknown_payload_fields:{','.join(unknown)}")
        trace.append(
            {
                "title": "Gateway 校验 action 参数",
                "actor": "Simple Trusted Gateway",
                "detail": "网关使用 DOIR action input schema 校验 payload，避免绕过 OSDK 传入非法字段。",
                "facts": {
                    "action_id": action_id,
                    "payload_fields": sorted(payload.keys()),
                    "internal_dependencies": action.get("depends_on", []),
                },
            }
        )

    def _success_response(
        self,
        envelope: Dict[str, Any],
        gateway_trace: List[Dict[str, Any]],
        job: ExecutionJob,
    ) -> Dict[str, Any]:
        receipt_id = job.receipt.request_id if job.receipt else None
        return {
            "request_id": envelope.get("request_id") or job.job_id,
            "status": "succeeded",
            "result": job.result,
            "receipt_id": receipt_id,
            "policy_decision": job.policy_decision.reason,
            "runtime_version": job.receipt.runtime_version if job.receipt else None,
            "job_id": job.job_id,
            "gateway": {
                "input_hash": sha256_json(envelope),
                "output_hash": sha256_json(job.result or {}),
            },
            "trace": gateway_trace
            + [
                {
                    "title": "Gateway 返回摘要和 Receipt",
                    "actor": "Simple Trusted Gateway",
                    "detail": "网关只把产品结果、receipt_id 和执行状态返回远程 OSDK。",
                    "facts": {
                        "receipt_id": receipt_id,
                        "returned_fields": sorted((job.result or {}).keys()),
                    },
                }
            ],
            "runtime_trace": job.trace,
            "receipt": job.receipt.model_dump(mode="json") if job.receipt else None,
        }

    def _denied(
        self,
        envelope: Dict[str, Any],
        trace: List[Dict[str, Any]],
        reason: str,
        *,
        job: Optional[ExecutionJob] = None,
    ) -> Dict[str, Any]:
        return {
            "request_id": envelope.get("request_id"),
            "status": "denied",
            "reason": reason,
            "error_code": reason,
            "result": None,
            "receipt_id": None,
            "policy_decision": reason,
            "job_id": job.job_id if job else None,
            "trace": trace,
        }

    @staticmethod
    def _required(envelope: Dict[str, Any], key: str) -> Any:
        value = envelope.get(key)
        if value in (None, ""):
            raise GatewayError(f"missing_{key}")
        return value
