from __future__ import annotations

from typing import Any, Dict

from .compiler import compile_all
from .models import ApplicationManifest
from .policy import EntitlementStore
from .registry import DOIRRegistryLite


class GatewayControlPlane:
    """Gateway-owned product catalog and entitlement state.

    This control plane deliberately does not import or load provider datasets.
    Provider data belongs to independently configured Provider Runtime processes.
    """

    def __init__(self) -> None:
        self.policy = EntitlementStore()
        self.registry = DOIRRegistryLite.seeded()
        self.products = compile_all(registry=self.registry)

    def create_entitlement(
        self,
        *,
        product_id: str,
        provider_id: str,
        data_subject: str,
        requester_agent: str,
    ) -> Dict[str, Any]:
        product = self.products[product_id]["product_manifest"]
        mapping = self.registry.get_provider_mapping(provider_id)
        if mapping["product_id"] != product_id:
            raise ValueError(f"provider_not_available_for_product:{provider_id}")
        entitlement = self.policy.create(
            product_id=product_id,
            purpose=product["purpose"],
            requester_agent=requester_agent,
            data_subject=data_subject,
            provider_id=provider_id,
            output_granularity=product["output_granularity"],
            expires_hours=24,
            max_calls=10,
        )
        return entitlement.model_dump(mode="json")

    def revoke_entitlement(self, entitlement_id: str) -> Dict[str, Any]:
        return self.policy.revoke(entitlement_id).model_dump(mode="json")

    def app_for_requester(self, product_id: str, requester_agent: str) -> ApplicationManifest:
        if product_id == "enterprise-energy-credit":
            return ApplicationManifest(
                app_id="remote-bank-risk-workload",
                version="1.0.0",
                digest="sha256:remote-bank-risk-workload-demo",
                requester_agent=requester_agent,
                allowed_products=[product_id],
            )
        if product_id == "changchun-excavation-risk":
            return ApplicationManifest(
                app_id="remote-excavation-risk-workload",
                version="1.0.0",
                digest="sha256:remote-excavation-risk-workload-demo",
                requester_agent=requester_agent,
                allowed_products=[product_id],
            )
        return ApplicationManifest(
            app_id="remote-product-workload",
            version="1.0.0",
            digest=f"sha256:{requester_agent}:{product_id}",
            requester_agent=requester_agent,
            allowed_products=[product_id],
        )
