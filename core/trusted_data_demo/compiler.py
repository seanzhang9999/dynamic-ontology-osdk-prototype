from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from .fixtures import build_changchun_doir, build_power_doir, product_definitions
from .models import ExposureLevel, OUTPUT_EXPOSURES, ProductPackage, READABLE_EXPOSURES


class CompileError(ValueError):
    pass


def _split_ref(ref: str) -> Tuple[str, str]:
    if "." not in ref:
        raise CompileError(f"Invalid field reference: {ref}")
    object_name, property_name = ref.split(".", 1)
    return object_name, property_name


def _property(doir: Dict[str, Any], ref: str) -> Dict[str, Any]:
    object_name, property_name = _split_ref(ref)
    try:
        return doir["object_types"][object_name]["properties"][property_name]
    except KeyError as exc:
        raise CompileError(f"Unknown product field: {ref}") from exc


def _exposure(doir: Dict[str, Any], ref: str) -> ExposureLevel:
    return ExposureLevel(_property(doir, ref)["exposure"])


def _output_schema(doir: Dict[str, Any], outputs: List[str]) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    for ref in outputs:
        object_name, property_name = _split_ref(ref)
        prop = _property(doir, ref)
        exposure = ExposureLevel(prop["exposure"])
        if exposure not in OUTPUT_EXPOSURES:
            raise CompileError(
                f"{ref} is {exposure.value} and cannot be emitted as product output"
            )
        properties[property_name] = {
            "title": property_name,
            "type": prop["type"],
            "source_object": object_name,
            "exposure": exposure.value,
        }
    return {"type": "object", "properties": properties, "additionalProperties": False}


def _readable_fields(doir: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields: List[Dict[str, Any]] = []
    for object_name, object_type in doir["object_types"].items():
        for property_name, prop in object_type["properties"].items():
            exposure = ExposureLevel(prop["exposure"])
            if exposure in READABLE_EXPOSURES:
                fields.append(
                    {
                        "object": object_name,
                        "property": property_name,
                        "type": prop["type"],
                        "exposure": exposure.value,
                    }
                )
    return fields


def _ontology_model(doir: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ontology": doir["ontology"],
        "object_types": doir.get("object_types", {}),
        "link_types": doir.get("link_types", {}),
        "query_types": doir.get("query_types", {}),
        "action_types": doir.get("action_types", {}),
        "product_projection": {
            "allowed_outputs": product["outputs"],
            "forbidden_outputs": product["forbidden_outputs"],
            "actions": product["actions"],
            "purpose": product["purpose"],
            "output_granularity": product["output_granularity"],
        },
    }


def _python_osdk(product: Dict[str, Any]) -> str:
    class_name = "".join(part.title() for part in product["id"].split("-")) + "Client"
    actions = "\n".join(
        f"    def {action}(self, **payload):\n"
        f"        return self.runtime.execute_action('{product['id']}', '{action}', payload)\n"
        for action in product["actions"]
    )
    return (
        f"class {class_name}:\n"
        f"    def __init__(self, runtime):\n"
        f"        self.runtime = runtime\n\n"
        f"{actions}"
    )


def _mcp_tools(product: Dict[str, Any], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    tools = [
        {
            "name": f"describe_{product['id'].replace('-', '_')}",
            "description": f"Describe product {product['id']}",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": f"request_{product['id'].replace('-', '_')}_entitlement",
            "description": "Request a purpose-bound entitlement",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data_subject": {"type": "string"},
                    "provider_id": {"type": "string"},
                },
                "required": ["data_subject", "provider_id"],
            },
        },
    ]
    for action in product["actions"]:
        tools.append(
            {
                "name": action,
                "description": f"Execute {action} through Provider Runtime",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": schema,
            }
        )
    return tools


def compile_product(
    product_id: str,
    *,
    coordinate_core: bool = False,
    extra_outputs: Optional[List[str]] = None,
) -> ProductPackage:
    products = product_definitions()
    if product_id not in products:
        raise CompileError(f"Unknown product: {product_id}")

    product = dict(products[product_id])
    if extra_outputs:
        product["outputs"] = product["outputs"] + extra_outputs

    if product_id == "enterprise-energy-credit":
        doir = build_power_doir()
    elif product_id == "changchun-excavation-risk":
        doir = build_changchun_doir(coordinate_core=coordinate_core)
        if coordinate_core:
            product["version"] = "1.1.0"
            product["ontology_version"] = "changchun-excavation-risk@1.1.0"
    else:
        raise CompileError(f"No DOIR fixture for product: {product_id}")

    for forbidden in product["forbidden_outputs"]:
        if forbidden in product["outputs"]:
            raise CompileError(f"{forbidden} is explicitly forbidden for product output")
        exposure = _exposure(doir, forbidden)
        if exposure == ExposureLevel.EXTERNAL_RESULT:
            raise CompileError(f"Forbidden field {forbidden} is incorrectly public")

    schema = _output_schema(doir, product["outputs"])
    readable_fields = _readable_fields(doir)
    mcp_tools = _mcp_tools(product, schema)
    product_version = f"{product['id']}@{product['version']}"

    product_manifest = {
        "id": product["id"],
        "version": product["version"],
        "product_version": product_version,
        "purpose": product["purpose"],
        "output_granularity": product["output_granularity"],
        "ontology": doir["ontology"],
        "actions": product["actions"],
        "readable_fields": readable_fields,
        "raw_export": False,
        "network_egress": False,
    }
    runtime_binding = {
        "product_id": product["id"],
        "product_version": product_version,
        "runtime_methods": product["actions"],
        "internal_dependencies": doir.get("action_types", {}),
    }
    quality_certificate = {
        "product_id": product["id"],
        "coverage": "synthetic-demo",
        "minimum_coverage_months": 12 if product_id == "enterprise-energy-credit" else None,
        "quality_gate": "passed",
    }
    compatibility_report = (
        f"# Compatibility report for {product_version}\n\n"
        "- Breaking changes: none for this demo release.\n"
        f"- Readable fields: {len(readable_fields)}\n"
        f"- Actions: {', '.join(product['actions'])}\n"
    )
    openapi = {
        "openapi": "3.1.0",
        "info": {"title": product["id"], "version": product["version"]},
        "paths": {
            f"/jobs/execute/{action}": {"post": {"responses": {"200": {"description": "OK"}}}}
            for action in product["actions"]
        },
    }
    return ProductPackage(
        product_manifest=product_manifest,
        ontology_model=_ontology_model(doir, product),
        product_schema=schema,
        runtime_binding=runtime_binding,
        quality_certificate=quality_certificate,
        compatibility_report=compatibility_report,
        python_osdk=_python_osdk(product),
        mcp_tools=mcp_tools,
        openapi=openapi,
    )


def compile_all(coordinate_core: bool = False) -> Dict[str, Dict[str, Any]]:
    return {
        "enterprise-energy-credit": compile_product(
            "enterprise-energy-credit"
        ).model_dump(mode="json"),
        "changchun-excavation-risk": compile_product(
            "changchun-excavation-risk", coordinate_core=coordinate_core
        ).model_dump(mode="json"),
    }


def package_as_json(product_id: str, coordinate_core: bool = False) -> str:
    package = compile_product(product_id, coordinate_core=coordinate_core)
    return json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2)
