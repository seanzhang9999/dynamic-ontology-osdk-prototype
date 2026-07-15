from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .models import ExposureLevel


PROVIDERS = {
    "grid": {
        "provider_agent": "agent:grid-runtime",
        "mapping_version": "grid-energy-mapping@1.0.0",
        "display_name": "国家电网 Provider Runtime",
    },
    "integrated-energy": {
        "provider_agent": "agent:integrated-energy-runtime",
        "mapping_version": "integrated-energy-mapping@1.0.0",
        "display_name": "综合能源 Provider Runtime",
    },
    "changchun": {
        "provider_agent": "agent:changchun-lifeline-runtime",
        "mapping_version": "changchun-lifeline-mapping@1.0.0",
        "display_name": "长春城市生命线 Provider Runtime",
    },
}


def _months() -> List[str]:
    return [f"2025-{month:02d}" for month in range(7, 13)] + [
        f"2026-{month:02d}" for month in range(1, 7)
    ]


def make_power_records(provider_id: str) -> List[Dict[str, Any]]:
    months = _months()
    records: List[Dict[str, Any]] = []
    for enterprise_index in range(1, 25):
        enterprise_id = f"91300000DEMO{enterprise_index:04d}"
        base = 8000 + enterprise_index * 270
        for month_index, period in enumerate(months):
            seasonal = ((month_index % 4) - 1.5) * 210
            provider_shift = 95 if provider_id == "integrated-energy" else 0
            late_days = 0
            if enterprise_index % 7 == 0 and month_index in {3, 9}:
                late_days = 12 + enterprise_index % 5
            if enterprise_index % 11 == 0 and month_index in {1, 5, 10}:
                late_days = 5
            records.append(
                {
                    "enterprise_id": enterprise_id,
                    "period": period,
                    "kwh": round(base + seasonal + provider_shift, 2),
                    "payment_status": "late" if late_days else "settled",
                    "late_days": late_days,
                    "source_row_id": f"{provider_id}-{enterprise_index}-{period}",
                }
            )
    return records


def make_changchun_assets() -> Dict[str, Any]:
    return {
        "pipeline_segments": [
            {
                "segment_id": "gas-001",
                "asset_type": "gas",
                "line": [[125.312, 43.884], [125.319, 43.889]],
                "depth": 2.2,
                "material": "steel",
                "age_years": 18,
                "risk_weight": 0.9,
            },
            {
                "segment_id": "water-014",
                "asset_type": "water",
                "line": [[125.318, 43.881], [125.325, 43.887]],
                "depth": 1.6,
                "material": "ductile_iron",
                "age_years": 12,
                "risk_weight": 0.6,
            },
            {
                "segment_id": "heat-021",
                "asset_type": "heating",
                "line": [[125.302, 43.878], [125.309, 43.882]],
                "depth": 2.8,
                "material": "composite",
                "age_years": 7,
                "risk_weight": 0.4,
            },
            {
                "segment_id": "power-033",
                "asset_type": "power",
                "line": [[125.314, 43.892], [125.327, 43.894]],
                "depth": 1.2,
                "material": "cable",
                "age_years": 10,
                "risk_weight": 0.7,
            },
        ],
        "historical_hazards": [
            {"asset_type": "gas", "count": 3, "severity": "high"},
            {"asset_type": "water", "count": 2, "severity": "medium"},
            {"asset_type": "heating", "count": 1, "severity": "low"},
        ],
        "monitoring_summary": {
            "gas": {"alerts_30d": 2, "quality": 0.97},
            "water": {"alerts_30d": 1, "quality": 0.96},
            "heating": {"alerts_30d": 0, "quality": 0.94},
            "power": {"alerts_30d": 1, "quality": 0.95},
        },
    }


def build_power_doir() -> Dict[str, Any]:
    return {
        "ontology": {
            "id": "enterprise-energy-credit",
            "version": "1.0.0",
            "display_name": "企业用电征信动态本体",
        },
        "object_types": {
            "Enterprise": {
                "properties": {
                    "enterprise_id": {
                        "type": "string",
                        "exposure": ExposureLevel.COMPUTE_ONLY.value,
                    },
                    "masked_name": {
                        "type": "string",
                        "exposure": ExposureLevel.MASKED.value,
                    },
                }
            },
            "EnergyUsage": {
                "properties": {
                    "period": {
                        "type": "string",
                        "exposure": ExposureLevel.INTERNAL_ONLY.value,
                    },
                    "kwh": {
                        "type": "number",
                        "exposure": ExposureLevel.COMPUTE_ONLY.value,
                    },
                    "raw_monthly_kwh": {
                        "type": "number[]",
                        "exposure": ExposureLevel.HIDDEN.value,
                    },
                }
            },
            "BillingRecord": {
                "properties": {
                    "payment_status": {
                        "type": "string",
                        "exposure": ExposureLevel.AGGREGATE_ONLY.value,
                    },
                    "late_days": {
                        "type": "number",
                        "exposure": ExposureLevel.AGGREGATE_ONLY.value,
                    },
                }
            },
            "CreditResult": {
                "properties": {
                    "credit_score": {
                        "type": "number",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "risk_level": {
                        "type": "string",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "coverage_months": {
                        "type": "number",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "usage_stability_index": {
                        "type": "number",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "late_payment_count_band": {
                        "type": "string",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "quality_summary": {
                        "type": "object",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "explanation": {
                        "type": "string",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                }
            },
        },
        "query_types": {
            "energy_usage_summary": {
                "returns": "CreditResult",
                "parameters": {"enterprise_id": "string", "months": "number"},
            }
        },
        "action_types": {
            "compute_credit_features": {
                "depends_on": ["EnergyUsage.kwh", "BillingRecord.late_days"],
                "returns": "CreditResult",
            }
        },
    }


def build_changchun_doir(coordinate_core: bool = False) -> Dict[str, Any]:
    coordinate_exposure = (
        ExposureLevel.COMPUTE_ONLY.value
        if coordinate_core
        else ExposureLevel.INTERNAL_ONLY.value
    )
    return {
        "ontology": {
            "id": "changchun-excavation-risk",
            "version": "1.0.0" if not coordinate_core else "1.1.0",
            "display_name": "长春城市生命线开挖风险动态本体",
        },
        "object_types": {
            "PipelineSegment": {
                "properties": {
                    "segment_id": {
                        "type": "string",
                        "exposure": ExposureLevel.INTERNAL_ONLY.value,
                    },
                    "exact_coordinates": {
                        "type": "LineString",
                        "exposure": coordinate_exposure,
                    },
                    "asset_type": {
                        "type": "string",
                        "exposure": ExposureLevel.AGGREGATE_ONLY.value,
                    },
                    "owner_detail": {
                        "type": "string",
                        "exposure": ExposureLevel.HIDDEN.value,
                    },
                }
            },
            "ExcavationProject": {
                "properties": {
                    "excavation_area": {
                        "type": "GeoJSON",
                        "exposure": ExposureLevel.COMPUTE_ONLY.value,
                    },
                    "excavation_depth": {
                        "type": "number",
                        "exposure": ExposureLevel.COMPUTE_ONLY.value,
                    },
                    "construction_method": {
                        "type": "string",
                        "exposure": ExposureLevel.COMPUTE_ONLY.value,
                    },
                }
            },
            "RiskAssessment": {
                "properties": {
                    "overall_risk": {
                        "type": "string",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "affected_asset_types": {
                        "type": "string[]",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "affected_segment_count": {
                        "type": "number",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "recommendations": {
                        "type": "string[]",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                    "quality_summary": {
                        "type": "object",
                        "exposure": ExposureLevel.EXTERNAL_RESULT.value,
                    },
                }
            },
        },
        "action_types": {
            "assess_excavation_risk": {
                "depends_on": [
                    "PipelineSegment.exact_coordinates",
                    "PipelineSegment.asset_type",
                    "ExcavationProject.excavation_area",
                ],
                "returns": "RiskAssessment",
            }
        },
    }


def product_definitions() -> Dict[str, Dict[str, Any]]:
    return {
        "enterprise-energy-credit": {
            "id": "enterprise-energy-credit",
            "version": "1.0.0",
            "purpose": "enterprise_credit_assessment",
            "output_granularity": "feature_summary",
            "ontology_version": "enterprise-energy-credit@1.0.0",
            "outputs": [
                "CreditResult.credit_score",
                "CreditResult.risk_level",
                "CreditResult.coverage_months",
                "CreditResult.usage_stability_index",
                "CreditResult.late_payment_count_band",
                "CreditResult.quality_summary",
                "CreditResult.explanation",
            ],
            "actions": ["compute_credit_features"],
            "forbidden_outputs": [
                "EnergyUsage.raw_monthly_kwh",
                "EnergyUsage.kwh",
                "BillingRecord.late_days",
            ],
        },
        "changchun-excavation-risk": {
            "id": "changchun-excavation-risk",
            "version": "1.0.0",
            "purpose": "construction_safety_assessment",
            "output_granularity": "risk_summary",
            "ontology_version": "changchun-excavation-risk@1.0.0",
            "outputs": [
                "RiskAssessment.overall_risk",
                "RiskAssessment.affected_asset_types",
                "RiskAssessment.affected_segment_count",
                "RiskAssessment.recommendations",
                "RiskAssessment.quality_summary",
            ],
            "actions": ["assess_excavation_risk"],
            "forbidden_outputs": [
                "PipelineSegment.exact_coordinates",
                "PipelineSegment.owner_detail",
            ],
        },
    }

