from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderBinding(BaseModel):
    """Logical Provider and its purpose-bound entitlement."""
    model_config = ConfigDict(extra="forbid")
    provider_id: str
    entitlement_id: str


class ComputeCreditFeaturesInput(BaseModel):
    """Shared business payload generated from DOIR action inputs."""
    model_config = ConfigDict(extra="forbid")
    enterprise_id: str = Field(description='Unified enterprise identifier selected by the requester.')
    months: int = Field(default=12, description='Number of recent months to summarize.')


class ComputeCreditFeaturesResult(BaseModel):
    """Result model generated from the product output schema."""
    model_config = ConfigDict(extra="allow")
    credit_score: Optional[float] = None
    risk_level: Optional[str] = None
    coverage_months: Optional[float] = None
    usage_stability_index: Optional[float] = None
    late_payment_count_band: Optional[str] = None
    quality_summary: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    receipt_id: Optional[str] = None
    request_id: Optional[str] = None
    policy_decision: Optional[str] = None
    runtime_version: Optional[str] = None


class ComputeCreditFeaturesProviderResult(BaseModel):
    """One Provider Runtime outcome returned by Gateway fan-out."""
    model_config = ConfigDict(extra="forbid")
    provider_id: str
    status: Literal["succeeded", "denied", "failed"]
    result: Optional[ComputeCreditFeaturesResult] = None
    error_code: Optional[str] = None
    receipt_id: Optional[str] = None
    runtime_version: Optional[str] = None
    job_id: Optional[str] = None
    policy_decision: Optional[str] = None
    runtime_trace: List[Dict[str, Any]] = Field(default_factory=list)
    receipt: Optional[Dict[str, Any]] = None


class ComputeCreditFeaturesMultiProviderResult(BaseModel):
    """Gateway fan-out response; business aggregation remains caller-owned."""
    model_config = ConfigDict(extra="forbid")
    request_id: Optional[str] = None
    status: Literal["completed", "partial", "failed"]
    product_id: str
    action_id: str
    provider_results: Dict[str, ComputeCreditFeaturesProviderResult]
    gateway: Dict[str, Any] = Field(default_factory=dict)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
