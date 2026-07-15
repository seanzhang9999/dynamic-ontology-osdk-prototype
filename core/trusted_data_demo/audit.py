from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, List, Union
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .models import ExecutionReceipt, PolicyDecision, utc_now


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


class AuditLog:
    def __init__(self) -> None:
        self._private_key = Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._events: List[Dict[str, Any]] = []
        self._previous_hash = "genesis"

    @property
    def public_key_b64(self) -> str:
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(public_bytes).decode("ascii")

    def create_receipt(
        self,
        *,
        purpose: str,
        requester_agent: str,
        provider_agent: str,
        data_subject: str,
        consent_digest: str,
        entitlement_id: str,
        application_digest: str,
        ontology_version: str,
        mapping_version: str,
        product_version: str,
        runtime_version: str,
        data_window: str,
        quality_snapshot: Dict[str, Any],
        request_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        policy_decision: PolicyDecision,
    ) -> ExecutionReceipt:
        payload = {
            "request_id": f"req_{uuid4().hex[:12]}",
            "purpose": purpose,
            "requester_agent": requester_agent,
            "provider_agent": provider_agent,
            "data_subject": data_subject,
            "consent_digest": consent_digest,
            "entitlement_id": entitlement_id,
            "application_digest": application_digest,
            "ontology_version": ontology_version,
            "mapping_version": mapping_version,
            "product_version": product_version,
            "runtime_version": runtime_version,
            "data_window": data_window,
            "quality_snapshot": quality_snapshot,
            "input_hash": sha256_json(request_payload),
            "output_hash": sha256_json(output_payload),
            "policy_decision": policy_decision.model_dump(mode="json"),
            "previous_event_hash": self._previous_hash,
            "provider_public_key": self.public_key_b64,
            "signature_algorithm": "Ed25519",
            "signed_at": utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        signature = self._private_key.sign(canonical_json(payload))
        payload["provider_signature"] = base64.b64encode(signature).decode("ascii")
        receipt = ExecutionReceipt.model_validate(payload)
        event_hash = sha256_json(receipt.model_dump(mode="json"))
        self._events.append({"hash": event_hash, "receipt": receipt.model_dump(mode="json")})
        self._previous_hash = event_hash
        return receipt

    @staticmethod
    def verify(receipt: Union[ExecutionReceipt, Dict[str, Any]]) -> bool:
        receipt_dict = (
            receipt.model_dump(mode="json")
            if isinstance(receipt, ExecutionReceipt)
            else dict(receipt)
        )
        signature_b64 = receipt_dict.pop("provider_signature")
        public_key_b64 = receipt_dict["provider_public_key"]
        signature = base64.b64decode(signature_b64)
        public_key_bytes = base64.b64decode(public_key_b64)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        try:
            public_key.verify(signature, canonical_json(receipt_dict))
            return True
        except InvalidSignature:
            return False

    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)
