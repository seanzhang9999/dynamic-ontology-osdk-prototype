from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComputeCreditFeaturesInput(BaseModel):
    """Input model generated from DOIR action_types inputs."""
    model_config = ConfigDict(extra="forbid")
    provider_id: str = Field(description='Provider Runtime route, for example grid or integrated-energy.')
    enterprise_id: str = Field(description='Unified enterprise identifier selected by the requester.')
    entitlement_id: str = Field(description='Purpose-bound authorization issued by Policy Service.')
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
