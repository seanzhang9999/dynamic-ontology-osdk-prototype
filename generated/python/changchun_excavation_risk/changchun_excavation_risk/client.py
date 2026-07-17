from __future__ import annotations

from typing import Any, Dict, List

from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient
from .models import (
    ProviderBinding,
    AssessExcavationRiskInput,
    AssessExcavationRiskResult,
    AssessExcavationRiskProviderResult,
    AssessExcavationRiskMultiProviderResult,
)


class ChangchunExcavationRiskClient:
    def __init__(self, runtime: ProviderRuntimeClient | AsyncProviderRuntimeClient) -> None:
        self.runtime = runtime

    def assess_excavation_risk(self, *, providers: List[ProviderBinding], project_id: str, excavation_area: Dict[str, Any], excavation_depth: float, construction_method: str) -> AssessExcavationRiskMultiProviderResult:
        """Assess excavation risk inside Changchun lifeline Runtime without exposing exact pipeline coordinates.

        Internal ontology dependencies used by Provider Runtime:
        - PipelineSegment.exact_coordinates
        - PipelineSegment.asset_type
        - ExcavationProject.excavation_area

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = AssessExcavationRiskInput(project_id=project_id, excavation_area=excavation_area, excavation_depth=excavation_depth, construction_method=construction_method)
        payload = request.model_dump(exclude_none=True)
        provider_values = [
            ProviderBinding.model_validate(item).model_dump() for item in providers
        ]
        response = self.runtime.execute_action(
            product_id='changchun-excavation-risk',
            action_id='assess_excavation_risk',
            providers=provider_values,
            purpose='construction_safety_assessment',
            product_version='changchun-excavation-risk@1.0.0',
            payload=payload,
        )
        return AssessExcavationRiskMultiProviderResult.model_validate(response)

    async def aassess_excavation_risk(self, *, providers: List[ProviderBinding], project_id: str, excavation_area: Dict[str, Any], excavation_depth: float, construction_method: str) -> AssessExcavationRiskMultiProviderResult:
        """Assess excavation risk inside Changchun lifeline Runtime without exposing exact pipeline coordinates.

        Internal ontology dependencies used by Provider Runtime:
        - PipelineSegment.exact_coordinates
        - PipelineSegment.asset_type
        - ExcavationProject.excavation_area

        These dependencies are not external parameters; the Runtime resolves them through provider mappings.
        """
        request = AssessExcavationRiskInput(project_id=project_id, excavation_area=excavation_area, excavation_depth=excavation_depth, construction_method=construction_method)
        payload = request.model_dump(exclude_none=True)
        provider_values = [
            ProviderBinding.model_validate(item).model_dump() for item in providers
        ]
        response = await self.runtime.execute_action(
            product_id='changchun-excavation-risk',
            action_id='assess_excavation_risk',
            providers=provider_values,
            purpose='construction_safety_assessment',
            product_version='changchun-excavation-risk@1.0.0',
            payload=payload,
        )
        return AssessExcavationRiskMultiProviderResult.model_validate(response)
