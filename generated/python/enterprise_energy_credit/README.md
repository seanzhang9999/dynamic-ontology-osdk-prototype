# enterprise-energy-credit Product OSDK

Generated from DOIR action schema. The SDK is a remote workload client: it calls a trusted gateway, not a database or internal Runtime object.

```python
from enterprise_energy_credit import EnterpriseEnergyCreditClient, ProviderRuntimeClient

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_bank_agent",
    requester_agent="agent:bank-risk",
)
client = EnterpriseEnergyCreditClient(runtime=runtime)
result = client.compute_credit_features(
    provider_id="grid",
    enterprise_id="demo",
    entitlement_id="ent_demo",
    months=12,
)
print(result.receipt_id)
```
