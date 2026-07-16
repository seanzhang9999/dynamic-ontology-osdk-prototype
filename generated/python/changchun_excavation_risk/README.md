# changchun-excavation-risk Product OSDK

Generated from DOIR action schema. The SDK is a remote workload client: it calls a trusted gateway, not a database or internal Runtime object.

```python
from changchun_excavation_risk import ChangchunExcavationRiskClient, ProviderRuntimeClient

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_construction_agent",
    requester_agent="agent:construction-safety",
)
client = ChangchunExcavationRiskClient(runtime=runtime)
result = client.assess_excavation_risk(
    project_id="demo",
    excavation_area={},
    excavation_depth=1.0,
    construction_method="demo",
    entitlement_id="ent_demo",
    provider_id="changchun",
)
print(result.receipt_id)
```
