# Demo Contract

## 企业用电征信可信数据产品

Purpose: `enterprise_credit_assessment`

Input:

- `enterprise_id`
- `months`
- `entitlement_id`
- signed application manifest

Allowed output:

- `credit_score`
- `risk_level`
- `coverage_months`
- `usage_stability_index`
- `late_payment_count_band`
- `provider_count`
- `quality_summary`
- `explanation`
- signed execution receipt

Forbidden output:

- raw monthly kWh rows
- exact payment ledger
- account or meter identifiers
- table names, source row IDs, connection strings

## 长春地下管线开挖风险评估可信数据产品

Purpose: `construction_safety_assessment`

Input:

- `project_id`
- `excavation_area`
- `excavation_depth`
- `construction_method`
- `entitlement_id`

Allowed output:

- `overall_risk`
- `affected_asset_types`
- `affected_segment_count`
- `recommendations`
- `quality_summary`
- signed execution receipt

Forbidden output:

- exact pipeline coordinates
- full utility network topology
- owner detail
- raw monitoring time series

