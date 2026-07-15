# Data Dictionary

## Power Credit

| Concept | Grid source | Integrated energy source | Exposure |
| --- | --- | --- | --- |
| Enterprise ID | `customer.unified_credit_code` | `enterprise.enterprise_no` | `COMPUTE_ONLY` |
| Usage month | `monthly_usage.usage_month` | `billing.period_code` | `INTERNAL_ONLY` |
| Monthly kWh | `monthly_usage.total_kwh` | `billing.energy_qty` | `COMPUTE_ONLY` |
| Payment status | `payment.status` | `charge.settle_status` | `AGGREGATE_ONLY` |
| Late days | `paid_date - due_date` | `settle_date - deadline` | `AGGREGATE_ONLY` |
| Credit score | local feature compute | local feature compute | `EXTERNAL_RESULT` |

The MVP generates 24 enterprises with 12 months of synthetic records per provider in `trusted_data_demo.fixtures`.

## Changchun Lifeline

| Concept | Source | Exposure |
| --- | --- | --- |
| Pipeline exact geometry | `gis.pipeline_layer.geometry` | `INTERNAL_ONLY`, upgraded to `COMPUTE_ONLY` in the recompile demo |
| Asset type | `gis.pipeline_layer.asset_type` | `AGGREGATE_ONLY` |
| Owner detail | `gis.pipeline_layer.owner` | `HIDDEN` |
| Excavation area | `permit.project_area` | `COMPUTE_ONLY` |
| Overall risk | local spatial rule | `EXTERNAL_RESULT` |

The MVP uses deterministic GeoJSON and bbox-buffer rules to prove the controlled product flow, not full GIS accuracy.

