# enterprise-energy-credit Product OSDK

Generated from DOIR action schema. The SDK is a remote workload client: it calls a trusted gateway, not a database or internal Runtime object.

```python
from enterprise_energy_credit import EnterpriseEnergyCreditClient, ProviderBinding, ProviderRuntimeClient

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_bank_agent",
    requester_agent="agent:bank-risk",
)
client = EnterpriseEnergyCreditClient(runtime=runtime)
providers = [
    ProviderBinding(provider_id="grid", entitlement_id="ent_grid"),
    ProviderBinding(provider_id="integrated-energy", entitlement_id="ent_energy"),
]
result = client.compute_credit_features(
    providers=providers,
    enterprise_id="demo",
    months=12,
)
for provider_id, provider_result in result.provider_results.items():
    print(provider_id, provider_result.status, provider_result.receipt_id)
```
