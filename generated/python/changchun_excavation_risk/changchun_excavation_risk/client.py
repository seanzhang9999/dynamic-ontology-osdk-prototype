from __future__ import annotations

from typing import Any, Dict

from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient
from .models import (
    AssessExcavationRiskInput,
    AssessExcavationRiskResult,
)


class ChangchunExcavationRiskClient:
    def __init__(self, runtime: ProviderRuntimeClient | AsyncProviderRuntimeClient) -> None:
        self.runtime = runtime

    def assess_excavation_risk(self, *, project_id: str, excavation_area: Dict[str, Any], excavation_depth: float, construction_method: str, entitlement_id: str, provider_id: str = 'changchun') -> AssessExcavationRiskResult:
        """Assess excavation risk inside Changchun lifeline Runtime without exposing exact pipeline coordinates.

        Internal ontology dependencies used by Provider Runtime:
        - PipelineSegment.exact_coordinates
        - PipelineSegment.asset_type
        - ExcavationProject.excavation_area

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = AssessExcavationRiskInput(project_id=project_id, excavation_area=excavation_area, excavation_depth=excavation_depth, construction_method=construction_method, entitlement_id=entitlement_id, provider_id=provider_id)
        payload = request.model_dump(exclude_none=True)
        provider_id_value = payload.pop('provider_id')
        entitlement_id_value = payload.pop('entitlement_id')
        response = self.runtime.execute_action(
            product_id='changchun-excavation-risk',
            action_id='assess_excavation_risk',
            provider_id=provider_id_value,
            entitlement_id=entitlement_id_value,
            purpose='construction_safety_assessment',
            product_version='changchun-excavation-risk@1.0.0',
            payload=payload,
        )
        result_payload = dict(response.get('result') or {})
        result_payload.update({
            'receipt_id': response.get('receipt_id'),
            'request_id': response.get('request_id'),
            'policy_decision': response.get('policy_decision'),
            'runtime_version': response.get('runtime_version'),
        })
        return AssessExcavationRiskResult.model_validate(result_payload)

    async def aassess_excavation_risk(self, *, project_id: str, excavation_area: Dict[str, Any], excavation_depth: float, construction_method: str, entitlement_id: str, provider_id: str = 'changchun') -> AssessExcavationRiskResult:
        """Assess excavation risk inside Changchun lifeline Runtime without exposing exact pipeline coordinates.

        Internal ontology dependencies used by Provider Runtime:
        - PipelineSegment.exact_coordinates
        - PipelineSegment.asset_type
        - ExcavationProject.excavation_area

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = AssessExcavationRiskInput(project_id=project_id, excavation_area=excavation_area, excavation_depth=excavation_depth, construction_method=construction_method, entitlement_id=entitlement_id, provider_id=provider_id)
        payload = request.model_dump(exclude_none=True)
        provider_id_value = payload.pop('provider_id')
        entitlement_id_value = payload.pop('entitlement_id')
        response = await self.runtime.execute_action(
            product_id='changchun-excavation-risk',
            action_id='assess_excavation_risk',
            provider_id=provider_id_value,
            entitlement_id=entitlement_id_value,
            purpose='construction_safety_assessment',
            product_version='changchun-excavation-risk@1.0.0',
            payload=payload,
        )
        result_payload = dict(response.get('result') or {})
        result_payload.update({
            'receipt_id': response.get('receipt_id'),
            'request_id': response.get('request_id'),
            'policy_decision': response.get('policy_decision'),
            'runtime_version': response.get('runtime_version'),
        })
        return AssessExcavationRiskResult.model_validate(result_payload)
