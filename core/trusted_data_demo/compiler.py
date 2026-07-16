from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import ExposureLevel, OUTPUT_EXPOSURES, ProductPackage, READABLE_EXPOSURES
from .osdk_generator import (
    action_input_schema,
    generate_python_sdk_files,
    python_osdk_preview,
    write_python_sdk_package,
)
from .registry import DOIRRegistryLite, RegistryError


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


def _action_schemas(doir: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
    schemas: Dict[str, Any] = {}
    for action_id in product["actions"]:
        try:
            action = dict(doir.get("action_types", {})[action_id])
        except KeyError as exc:
            raise CompileError(f"Unknown product action in DOIR: {action_id}") from exc
        if "inputs" not in action:
            raise CompileError(f"Action {action_id} must define inputs for dynamic OSDK generation")
        schemas[action_id] = action
    return schemas


def _mcp_tools(
    product: Dict[str, Any], schema: Dict[str, Any], action_schemas: Dict[str, Any]
) -> List[Dict[str, Any]]:
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
        action_schema = action_schemas[action]
        tools.append(
            {
                "name": action,
                "description": action_schema.get(
                    "description", f"Execute {action} through Provider Runtime"
                ),
                "input_schema": action_input_schema(action_schema),
                "output_schema": schema,
            }
        )
    return tools


def compile_product(
    product_id: str,
    *,
    coordinate_core: bool = False,
    extra_outputs: Optional[List[str]] = None,
    registry: Optional[DOIRRegistryLite] = None,
) -> ProductPackage:
    registry = registry or DOIRRegistryLite.seeded(coordinate_core=coordinate_core)
    try:
        product = dict(registry.get_product(product_id))
    except RegistryError as exc:
        raise CompileError(f"Unknown product: {product_id}")
    doir = registry.get_doir(product_id)
    if extra_outputs:
        product["outputs"] = product["outputs"] + extra_outputs

    for forbidden in product["forbidden_outputs"]:
        if forbidden in product["outputs"]:
            raise CompileError(f"{forbidden} is explicitly forbidden for product output")
        exposure = _exposure(doir, forbidden)
        if exposure == ExposureLevel.EXTERNAL_RESULT:
            raise CompileError(f"Forbidden field {forbidden} is incorrectly public")

    schema = _output_schema(doir, product["outputs"])
    readable_fields = _readable_fields(doir)
    action_schemas = _action_schemas(doir, product)
    mcp_tools = _mcp_tools(product, schema, action_schemas)
    product_version = f"{product['id']}@{product['version']}"
    sdk_files = generate_python_sdk_files(product, action_schemas, schema)
    python_osdk = python_osdk_preview(product, action_schemas, schema)

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
        "provider_mappings": registry.list_provider_mappings(),
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
            f"/actions/execute/{action}": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": action_input_schema(action_schemas[action])}
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
            for action in product["actions"]
        },
    }
    package = ProductPackage(
        product_manifest=product_manifest,
        ontology_model=_ontology_model(doir, product),
        product_schema=schema,
        action_schemas=action_schemas,
        runtime_binding=runtime_binding,
        quality_certificate=quality_certificate,
        compatibility_report=compatibility_report,
        python_osdk=python_osdk,
        sdk_files=sdk_files,
        mcp_tools=mcp_tools,
        openapi=openapi,
    )
    registry.save_compile_artifact(
        product_id, product_version, package.model_dump(mode="json")
    )
    return package


def compile_all(
    coordinate_core: bool = False,
    registry: Optional[DOIRRegistryLite] = None,
) -> Dict[str, Dict[str, Any]]:
    registry = registry or DOIRRegistryLite.seeded(coordinate_core=coordinate_core)
    return {
        "enterprise-energy-credit": compile_product(
            "enterprise-energy-credit", registry=registry
        ).model_dump(mode="json"),
        "changchun-excavation-risk": compile_product(
            "changchun-excavation-risk",
            coordinate_core=coordinate_core,
            registry=registry,
        ).model_dump(mode="json"),
    }


def package_as_json(product_id: str, coordinate_core: bool = False) -> str:
    package = compile_product(product_id, coordinate_core=coordinate_core)
    return json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2)


def write_python_sdk_packages(
    out_dir: str | Path = "generated/python",
    *,
    coordinate_core: bool = False,
) -> Dict[str, str]:
    registry = DOIRRegistryLite.seeded(coordinate_core=coordinate_core)
    out_path = Path(out_dir)
    written: Dict[str, str] = {}
    for product_id in ("enterprise-energy-credit", "changchun-excavation-risk"):
        package = compile_product(
            product_id, coordinate_core=coordinate_core, registry=registry
        )
        product = package.product_manifest
        product_for_generator = {
            "id": product["id"],
            "version": product["version"],
            "purpose": product["purpose"],
        }
        path = write_python_sdk_package(out_path, product_for_generator, package.sdk_files)
        written[product_id] = str(path)
    return written
