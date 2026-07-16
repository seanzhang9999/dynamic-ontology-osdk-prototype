from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ExposureLevel(str, Enum):
    HIDDEN = "HIDDEN"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    COMPUTE_ONLY = "COMPUTE_ONLY"
    MASKED = "MASKED"
    AGGREGATE_ONLY = "AGGREGATE_ONLY"
    EXTERNAL_RESULT = "EXTERNAL_RESULT"


READABLE_EXPOSURES = {
    ExposureLevel.MASKED,
    ExposureLevel.AGGREGATE_ONLY,
    ExposureLevel.EXTERNAL_RESULT,
}

OUTPUT_EXPOSURES = {
    ExposureLevel.MASKED,
    ExposureLevel.AGGREGATE_ONLY,
    ExposureLevel.EXTERNAL_RESULT,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductPackage(BaseModel):
    product_manifest: Dict[str, Any]
    ontology_model: Dict[str, Any]
    product_schema: Dict[str, Any]
    action_schemas: Dict[str, Any] = Field(default_factory=dict)
    runtime_binding: Dict[str, Any]
    quality_certificate: Dict[str, Any]
    compatibility_report: str
    python_osdk: str
    sdk_files: Dict[str, str] = Field(default_factory=dict)
    mcp_tools: List[Dict[str, Any]]
    openapi: Dict[str, Any]


class Entitlement(BaseModel):
    entitlement_id: str
    product_id: str
    purpose: str
    requester_agent: str
    data_subject: str
    provider_id: str
    output_granularity: str
    expires_at: datetime
    revoked: bool = False
    max_calls: int = 10
    used_calls: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    raw_export: bool = False
    network_egress: bool = False
    output_granularity: Optional[str] = None
    entitlement_id: Optional[str] = None


class ApplicationManifest(BaseModel):
    app_id: str
    version: str
    digest: str
    requester_agent: str
    allowed_products: List[str]


class ExecutionReceipt(BaseModel):
    request_id: str
    purpose: str
    requester_agent: str
    provider_agent: str
    data_subject: str
    consent_digest: str
    entitlement_id: str
    application_digest: str
    ontology_version: str
    mapping_version: str
    product_version: str
    runtime_version: str
    data_window: str
    quality_snapshot: Dict[str, Any]
    input_hash: str
    output_hash: str
    policy_decision: Dict[str, Any]
    previous_event_hash: str
    provider_signature: str
    provider_public_key: str
    signature_algorithm: Literal["Ed25519"]
    signed_at: datetime


class ExecutionJob(BaseModel):
    job_id: str
    product_id: str
    provider_id: str
    status: Literal["success", "denied", "failed"]
    result: Optional[Dict[str, Any]] = None
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    receipt: Optional[ExecutionReceipt] = None
    policy_decision: PolicyDecision
    created_at: datetime = Field(default_factory=utc_now)
