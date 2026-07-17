from __future__ import annotations

from typing import Any, Dict, List

from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient
from .models import (
    ProviderBinding,
    ComputeCreditFeaturesInput,
    ComputeCreditFeaturesResult,
    ComputeCreditFeaturesProviderResult,
    ComputeCreditFeaturesMultiProviderResult,
)


class EnterpriseEnergyCreditClient:
    def __init__(self, runtime: ProviderRuntimeClient | AsyncProviderRuntimeClient) -> None:
        self.runtime = runtime

    def compute_credit_features(self, *, providers: List[ProviderBinding], enterprise_id: str, months: int = 12) -> ComputeCreditFeaturesMultiProviderResult:
        """Compute purpose-bound enterprise energy credit features inside a Provider Runtime.

        Internal ontology dependencies used by Provider Runtime:
        - EnergyUsage.kwh
        - BillingRecord.late_days

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = ComputeCreditFeaturesInput(enterprise_id=enterprise_id, months=months)
        payload = request.model_dump(exclude_none=True)
        provider_values = [
            ProviderBinding.model_validate(item).model_dump() for item in providers
        ]
        response = self.runtime.execute_action(
            product_id='enterprise-energy-credit',
            action_id='compute_credit_features',
            providers=provider_values,
            purpose='enterprise_credit_assessment',
            product_version='enterprise-energy-credit@1.0.0',
            payload=payload,
        )
        return ComputeCreditFeaturesMultiProviderResult.model_validate(response)

    async def acompute_credit_features(self, *, providers: List[ProviderBinding], enterprise_id: str, months: int = 12) -> ComputeCreditFeaturesMultiProviderResult:
        """Compute purpose-bound enterprise energy credit features inside a Provider Runtime.

        Internal ontology dependencies used by Provider Runtime:
        - EnergyUsage.kwh
        - BillingRecord.late_days

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = ComputeCreditFeaturesInput(enterprise_id=enterprise_id, months=months)
        payload = request.model_dump(exclude_none=True)
        provider_values = [
            ProviderBinding.model_validate(item).model_dump() for item in providers
        ]
        response = await self.runtime.execute_action(
            product_id='enterprise-energy-credit',
            action_id='compute_credit_features',
            providers=provider_values,
            purpose='enterprise_credit_assessment',
            product_version='enterprise-energy-credit@1.0.0',
            payload=payload,
        )
        return ComputeCreditFeaturesMultiProviderResult.model_validate(response)
