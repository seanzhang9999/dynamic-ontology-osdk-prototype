from __future__ import annotations

from typing import Any, Dict

from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient
from .models import (
    ComputeCreditFeaturesInput,
    ComputeCreditFeaturesResult,
)


class EnterpriseEnergyCreditClient:
    def __init__(self, runtime: ProviderRuntimeClient | AsyncProviderRuntimeClient) -> None:
        self.runtime = runtime

    def compute_credit_features(self, *, provider_id: str, enterprise_id: str, entitlement_id: str, months: int = 12) -> ComputeCreditFeaturesResult:
        """Compute purpose-bound enterprise energy credit features inside a Provider Runtime.

        Internal ontology dependencies used by Provider Runtime:
        - EnergyUsage.kwh
        - BillingRecord.late_days

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = ComputeCreditFeaturesInput(provider_id=provider_id, enterprise_id=enterprise_id, entitlement_id=entitlement_id, months=months)
        payload = request.model_dump(exclude_none=True)
        provider_id_value = payload.pop('provider_id')
        entitlement_id_value = payload.pop('entitlement_id')
        response = self.runtime.execute_action(
            product_id='enterprise-energy-credit',
            action_id='compute_credit_features',
            provider_id=provider_id_value,
            entitlement_id=entitlement_id_value,
            purpose='enterprise_credit_assessment',
            product_version='enterprise-energy-credit@1.0.0',
            payload=payload,
        )
        result_payload = dict(response.get('result') or {})
        result_payload.update({
            'receipt_id': response.get('receipt_id'),
            'request_id': response.get('request_id'),
            'policy_decision': response.get('policy_decision'),
            'runtime_version': response.get('runtime_version'),
        })
        return ComputeCreditFeaturesResult.model_validate(result_payload)

    async def acompute_credit_features(self, *, provider_id: str, enterprise_id: str, entitlement_id: str, months: int = 12) -> ComputeCreditFeaturesResult:
        """Compute purpose-bound enterprise energy credit features inside a Provider Runtime.

        Internal ontology dependencies used by Provider Runtime:
        - EnergyUsage.kwh
        - BillingRecord.late_days

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = ComputeCreditFeaturesInput(provider_id=provider_id, enterprise_id=enterprise_id, entitlement_id=entitlement_id, months=months)
        payload = request.model_dump(exclude_none=True)
        provider_id_value = payload.pop('provider_id')
        entitlement_id_value = payload.pop('entitlement_id')
        response = await self.runtime.execute_action(
            product_id='enterprise-energy-credit',
            action_id='compute_credit_features',
            provider_id=provider_id_value,
            entitlement_id=entitlement_id_value,
            purpose='enterprise_credit_assessment',
            product_version='enterprise-energy-credit@1.0.0',
            payload=payload,
        )
        result_payload = dict(response.get('result') or {})
        result_payload.update({
            'receipt_id': response.get('receipt_id'),
            'request_id': response.get('request_id'),
            'policy_decision': response.get('policy_decision'),
            'runtime_version': response.get('runtime_version'),
        })
        return ComputeCreditFeaturesResult.model_validate(result_payload)
