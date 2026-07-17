# changchun-excavation-risk Product OSDK

Generated from DOIR action schema. The SDK is a remote workload client: it calls a trusted gateway, not a database or internal Runtime object.

```python
from changchun_excavation_risk import ChangchunExcavationRiskClient, ProviderBinding, ProviderRuntimeClient

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_construction_agent",
    requester_agent="agent:construction-safety",
)
client = ChangchunExcavationRiskClient(runtime=runtime)
providers = [
    ProviderBinding(provider_id="changchun", entitlement_id="ent_changchun"),
]
result = client.assess_excavation_risk(
    providers=providers,
    project_id="demo",
    excavation_area={},
    excavation_depth=1.0,
    construction_method="demo",
)
for provider_id, provider_result in result.provider_results.items():
    print(provider_id, provider_result.status, provider_result.receipt_id)
```
