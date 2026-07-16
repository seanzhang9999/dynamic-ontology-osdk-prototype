from __future__ import annotations

from datetime import timedelta
from typing import Dict, Optional
from uuid import uuid4

from .models import Entitlement, PolicyDecision, utc_now


class EntitlementStore:
    def __init__(self) -> None:
        self._entitlements: Dict[str, Entitlement] = {}

    def create(
        self,
        *,
        product_id: str,
        purpose: str,
        requester_agent: str,
        data_subject: str,
        provider_id: str,
        output_granularity: str,
        expires_hours: int = 24,
        max_calls: int = 10,
    ) -> Entitlement:
        entitlement = Entitlement(
            entitlement_id=f"ent_{uuid4().hex[:12]}",
            product_id=product_id,
            purpose=purpose,
            requester_agent=requester_agent,
            data_subject=data_subject,
            provider_id=provider_id,
            output_granularity=output_granularity,
            expires_at=utc_now() + timedelta(hours=expires_hours),
            max_calls=max_calls,
        )
        self._entitlements[entitlement.entitlement_id] = entitlement
        return entitlement

    def get(self, entitlement_id: str) -> Optional[Entitlement]:
        return self._entitlements.get(entitlement_id)

    def revoke(self, entitlement_id: str) -> Entitlement:
        entitlement = self._entitlements[entitlement_id]
        entitlement.revoked = True
        return entitlement

    def evaluate(
        self,
        *,
        entitlement_id: str,
        product_id: str,
        purpose: str,
        requester_agent: str,
        provider_id: str,
        output_granularity: str,
        consume: bool = True,
    ) -> PolicyDecision:
        entitlement = self.get(entitlement_id)
        if not entitlement:
            return PolicyDecision(allowed=False, reason="entitlement_not_found")
        if entitlement.revoked:
            return PolicyDecision(
                allowed=False,
                reason="entitlement_revoked",
                entitlement_id=entitlement.entitlement_id,
            )
        if entitlement.expires_at <= utc_now():
            return PolicyDecision(
                allowed=False,
                reason="entitlement_expired",
                entitlement_id=entitlement.entitlement_id,
            )
        checks = {
            "product_mismatch": entitlement.product_id == product_id,
            "purpose_mismatch": entitlement.purpose == purpose,
            "requester_mismatch": entitlement.requester_agent == requester_agent,
            "provider_mismatch": entitlement.provider_id == provider_id,
            "granularity_mismatch": entitlement.output_granularity == output_granularity,
            "quota_exceeded": entitlement.used_calls < entitlement.max_calls,
        }
        for reason, passed in checks.items():
            if not passed:
                return PolicyDecision(
                    allowed=False,
                    reason=reason,
                    entitlement_id=entitlement.entitlement_id,
                    output_granularity=entitlement.output_granularity,
                )
        if consume:
            entitlement.used_calls += 1
        return PolicyDecision(
            allowed=True,
            reason="allowed",
            raw_export=False,
            network_egress=False,
            output_granularity=entitlement.output_granularity,
            entitlement_id=entitlement.entitlement_id,
        )

    def all(self) -> Dict[str, Entitlement]:
        return dict(self._entitlements)
