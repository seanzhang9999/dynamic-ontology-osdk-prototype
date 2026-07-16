from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class AdapterError(ValueError):
    pass


class OntologyFieldAdapter(ABC):
    adapter_type: str

    def __init__(self, mapping: Dict[str, Any]) -> None:
        self.mapping = mapping

    @abstractmethod
    def describe(self) -> Dict[str, str]:
        """Return ontology-field to provider-source mapping for trace and audit."""

    def require_fields(self, *field_refs: str) -> None:
        missing = [field for field in field_refs if field not in self.mapping.get("fields", {})]
        if missing:
            raise AdapterError(
                f"provider_mapping_missing_fields:{self.mapping.get('provider_id')}:{missing}"
            )


class SQLFieldAdapter(OntologyFieldAdapter):
    adapter_type = "sql"

    def describe(self) -> Dict[str, str]:
        return dict(self.mapping.get("fields", {}))


class GISFieldAdapter(OntologyFieldAdapter):
    adapter_type = "gis"

    def describe(self) -> Dict[str, str]:
        return dict(self.mapping.get("fields", {}))


class RESTFieldAdapter(OntologyFieldAdapter):
    adapter_type = "rest"

    def describe(self) -> Dict[str, str]:
        return dict(self.mapping.get("fields", {}))


def adapter_for(mapping: Dict[str, Any]) -> OntologyFieldAdapter:
    adapter_type = mapping.get("adapter")
    if adapter_type == "sql":
        return SQLFieldAdapter(mapping)
    if adapter_type == "gis":
        return GISFieldAdapter(mapping)
    if adapter_type == "rest":
        return RESTFieldAdapter(mapping)
    raise AdapterError(f"unsupported_adapter:{adapter_type}")
