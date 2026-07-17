from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderBinding(BaseModel):
    """Logical Provider and its purpose-bound entitlement."""
    model_config = ConfigDict(extra="forbid")
    provider_id: str
    entitlement_id: str


class AssessExcavationRiskInput(BaseModel):
    """Shared business payload generated from DOIR action inputs."""
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(description='Construction or excavation project identifier.')
    excavation_area: Dict[str, Any] = Field(description='GeoJSON polygon submitted by the requester.')
    excavation_depth: float = Field(description='Excavation depth in meters.')
    construction_method: str = Field(description='Construction method, for example MECHANICAL or MANUAL.')


class AssessExcavationRiskResult(BaseModel):
    """Result model generated from the product output schema."""
    model_config = ConfigDict(extra="allow")
    overall_risk: Optional[str] = None
    affected_asset_types: Optional[List[str]] = None
    affected_segment_count: Optional[float] = None
    recommendations: Optional[List[str]] = None
    quality_summary: Optional[Dict[str, Any]] = None
    receipt_id: Optional[str] = None
    request_id: Optional[str] = None
    policy_decision: Optional[str] = None
    runtime_version: Optional[str] = None


class AssessExcavationRiskProviderResult(BaseModel):
    """One Provider Runtime outcome returned by Gateway fan-out."""
    model_config = ConfigDict(extra="forbid")
    provider_id: str
    status: Literal["succeeded", "denied", "failed"]
    result: Optional[AssessExcavationRiskResult] = None
    error_code: Optional[str] = None
    receipt_id: Optional[str] = None
    runtime_version: Optional[str] = None
    job_id: Optional[str] = None
    policy_decision: Optional[str] = None
    runtime_trace: List[Dict[str, Any]] = Field(default_factory=list)
    receipt: Optional[Dict[str, Any]] = None


class AssessExcavationRiskMultiProviderResult(BaseModel):
    """Gateway fan-out response; business aggregation remains caller-owned."""
    model_config = ConfigDict(extra="forbid")
    request_id: Optional[str] = None
    status: Literal["completed", "partial", "failed"]
    product_id: str
    action_id: str
    provider_results: Dict[str, AssessExcavationRiskProviderResult]
    gateway: Dict[str, Any] = Field(default_factory=dict)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
