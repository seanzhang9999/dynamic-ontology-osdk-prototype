from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def package_name(product_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", product_id).strip("_").lower()


def class_name_from_id(value: str, suffix: str = "") -> str:
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[^a-zA-Z0-9]+", value) if part) + suffix


def _py_type(type_name: str) -> str:
    mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "object": "Dict[str, Any]",
        "GeoJSON": "Dict[str, Any]",
        "LineString": "Dict[str, Any]",
        "string[]": "List[str]",
        "number[]": "List[float]",
    }
    return mapping.get(type_name, "Any")


def _json_schema_type(type_name: str) -> Dict[str, Any]:
    mapping: Dict[str, Dict[str, Any]] = {
        "string": {"type": "string"},
        "number": {"type": "number"},
        "integer": {"type": "integer"},
        "boolean": {"type": "boolean"},
        "object": {"type": "object"},
        "GeoJSON": {"type": "object"},
        "LineString": {"type": "object"},
        "string[]": {"type": "array", "items": {"type": "string"}},
        "number[]": {"type": "array", "items": {"type": "number"}},
    }
    return dict(mapping.get(type_name, {"type": "object"}))


def _default_code(spec: Dict[str, Any]) -> str:
    if "default" in spec:
        return repr(spec["default"])
    return "None"


def _is_required(spec: Dict[str, Any]) -> bool:
    return bool(spec.get("required", True)) and "default" not in spec


def _ordered_inputs(action: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    inputs = list(action.get("inputs", {}).items())
    required = [(name, spec) for name, spec in inputs if _is_required(spec)]
    optional = [(name, spec) for name, spec in inputs if not _is_required(spec)]
    return required + optional


def _business_inputs(action: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    return [
        (name, spec)
        for name, spec in _ordered_inputs(action)
        if spec.get("transport") != "envelope"
    ]


def action_input_schema(action: Dict[str, Any]) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for name, spec in action.get("inputs", {}).items():
        field_schema = _json_schema_type(spec.get("type", "object"))
        if spec.get("description"):
            field_schema["description"] = spec["description"]
        if "default" in spec:
            field_schema["default"] = spec["default"]
        if spec.get("transport"):
            field_schema["x-transport"] = spec["transport"]
        properties[name] = field_schema
        if _is_required(spec):
            required.append(name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _render_models(product: Dict[str, Any], action_schemas: Dict[str, Any], output_schema: Dict[str, Any]) -> str:
    blocks = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict, List, Literal, Optional",
        "",
        "from pydantic import BaseModel, ConfigDict, Field",
        "",
        "",
        "class ProviderBinding(BaseModel):",
        '    """Logical Provider and its purpose-bound entitlement."""',
        '    model_config = ConfigDict(extra="forbid")',
        "    provider_id: str",
        "    entitlement_id: str",
        "",
        "",
    ]
    for action_id, action in action_schemas.items():
        input_cls = class_name_from_id(action_id, "Input")
        result_cls = class_name_from_id(action_id, "Result")
        provider_result_cls = class_name_from_id(action_id, "ProviderResult")
        multi_result_cls = class_name_from_id(action_id, "MultiProviderResult")
        blocks.append(f"class {input_cls}(BaseModel):")
        blocks.append('    """Shared business payload generated from DOIR action inputs."""')
        blocks.append("    model_config = ConfigDict(extra=\"forbid\")")
        for name, spec in _business_inputs(action):
            py_type = _py_type(spec.get("type", "object"))
            description = spec.get("description", "")
            if _is_required(spec):
                blocks.append(f"    {name}: {py_type} = Field(description={description!r})")
            else:
                blocks.append(
                    f"    {name}: {py_type} = Field(default={_default_code(spec)}, description={description!r})"
                )
        if not _business_inputs(action):
            blocks.append("    pass")
        blocks.append("")
        blocks.append("")
        blocks.append(f"class {result_cls}(BaseModel):")
        blocks.append('    """Result model generated from the product output schema."""')
        blocks.append("    model_config = ConfigDict(extra=\"allow\")")
        for name, spec in output_schema.get("properties", {}).items():
            py_type = _py_type(spec.get("type", "object"))
            blocks.append(f"    {name}: Optional[{py_type}] = None")
        blocks.append("    receipt_id: Optional[str] = None")
        blocks.append("    request_id: Optional[str] = None")
        blocks.append("    policy_decision: Optional[str] = None")
        blocks.append("    runtime_version: Optional[str] = None")
        blocks.append("")
        blocks.append("")
        blocks.append(f"class {provider_result_cls}(BaseModel):")
        blocks.append('    """One Provider Runtime outcome returned by Gateway fan-out."""')
        blocks.append('    model_config = ConfigDict(extra="forbid")')
        blocks.append("    provider_id: str")
        blocks.append('    status: Literal["succeeded", "denied", "failed"]')
        blocks.append(f"    result: Optional[{result_cls}] = None")
        blocks.append("    error_code: Optional[str] = None")
        blocks.append("    receipt_id: Optional[str] = None")
        blocks.append("    runtime_version: Optional[str] = None")
        blocks.append("    job_id: Optional[str] = None")
        blocks.append("    policy_decision: Optional[str] = None")
        blocks.append("    runtime_trace: List[Dict[str, Any]] = Field(default_factory=list)")
        blocks.append("    receipt: Optional[Dict[str, Any]] = None")
        blocks.append("")
        blocks.append("")
        blocks.append(f"class {multi_result_cls}(BaseModel):")
        blocks.append('    """Gateway fan-out response; business aggregation remains caller-owned."""')
        blocks.append('    model_config = ConfigDict(extra="forbid")')
        blocks.append("    request_id: Optional[str] = None")
        blocks.append('    status: Literal["completed", "partial", "failed"]')
        blocks.append("    product_id: str")
        blocks.append("    action_id: str")
        blocks.append(f"    provider_results: Dict[str, {provider_result_cls}]")
        blocks.append("    gateway: Dict[str, Any] = Field(default_factory=dict)")
        blocks.append("    trace: List[Dict[str, Any]] = Field(default_factory=list)")
        blocks.append("")
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def _render_errors() -> str:
    return textwrap.dedent(
        '''
        from __future__ import annotations


        class ProviderRuntimeClientError(RuntimeError):
            def __init__(self, message: str, *, status_code: int | None = None, detail: object | None = None) -> None:
                super().__init__(message)
                self.status_code = status_code
                self.detail = detail


        class PolicyDenied(ProviderRuntimeClientError):
            pass


        class EntitlementExpired(PolicyDenied):
            pass


        class RuntimeUnavailable(ProviderRuntimeClientError):
            pass


        class ContractViolation(ProviderRuntimeClientError):
            pass
        '''
    ).lstrip()


def _render_runtime() -> str:
    return textwrap.dedent(
        '''
        from __future__ import annotations

        import asyncio
        import json
        from datetime import datetime, timezone
        from typing import Any, Dict, List, Optional
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen
        from uuid import uuid4

        from .errors import (
            ContractViolation,
            EntitlementExpired,
            PolicyDenied,
            ProviderRuntimeClientError,
            RuntimeUnavailable,
        )


        class ProviderRuntimeClient:
            """Remote client for Product OSDK workloads.

            The generated Product OSDK never receives a database handle or an
            internal Runtime object. It sends a signed/identified product action
            envelope to a trusted gateway, and the gateway routes to Provider
            Runtime after policy checks.
            """

            def __init__(
                self,
                *,
                base_url: str,
                api_key: str,
                requester_agent: str,
                timeout: float = 20,
                default_purpose: Optional[str] = None,
            ) -> None:
                self.base_url = base_url.rstrip("/")
                self.api_key = api_key
                self.requester_agent = requester_agent
                self.timeout = timeout
                self.default_purpose = default_purpose

            def execute_action(
                self,
                *,
                product_id: str,
                action_id: str,
                payload: Dict[str, Any],
                purpose: str,
                providers: Optional[List[Dict[str, str]]] = None,
                provider_id: Optional[str] = None,
                entitlement_id: Optional[str] = None,
                product_version: Optional[str] = None,
            ) -> Dict[str, Any]:
                envelope = {
                    "request_id": f"req_{uuid4().hex[:12]}",
                    "requester_agent": self.requester_agent,
                    "product_id": product_id,
                    "product_version": product_version,
                    "action_id": action_id,
                    "purpose": purpose or self.default_purpose,
                    "payload": payload,
                    "client_timestamp": datetime.now(timezone.utc).isoformat(),
                }
                if providers is not None:
                    envelope["providers"] = providers
                else:
                    if not provider_id or not entitlement_id:
                        raise ValueError("providers or provider_id/entitlement_id are required")
                    envelope["provider_id"] = provider_id
                    envelope["entitlement_id"] = entitlement_id
                return self._post("/actions/execute", envelope)

            def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
                data = json.dumps(body).encode("utf-8")
                request = Request(
                    self.base_url + path,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.api_key,
                    },
                    method="POST",
                )
                try:
                    with urlopen(request, timeout=self.timeout) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                except HTTPError as exc:
                    detail = _read_error_detail(exc)
                    _raise_for_gateway_error(exc.code, detail)
                except URLError as exc:
                    raise RuntimeUnavailable(str(exc)) from exc
                _raise_for_gateway_error(200, payload)
                return payload


        class AsyncProviderRuntimeClient:
            def __init__(self, **kwargs: Any) -> None:
                self._sync = ProviderRuntimeClient(**kwargs)

            async def execute_action(self, **kwargs: Any) -> Dict[str, Any]:
                return await asyncio.to_thread(self._sync.execute_action, **kwargs)


        def _read_error_detail(exc: HTTPError) -> Any:
            try:
                return json.loads(exc.read().decode("utf-8"))
            except Exception:
                return {"detail": str(exc)}


        def _raise_for_gateway_error(status_code: int, payload: Any) -> None:
            if not isinstance(payload, dict):
                return
            status = payload.get("status")
            detail = payload.get("detail", payload)
            reason = payload.get("error_code") or payload.get("reason")
            if isinstance(detail, dict):
                reason = reason or detail.get("error_code") or detail.get("reason")
                status = status or detail.get("status")
            if status == "denied" or status_code in {401, 403}:
                if reason == "entitlement_expired":
                    raise EntitlementExpired("entitlement expired", status_code=status_code, detail=detail)
                raise PolicyDenied(str(reason or "policy denied"), status_code=status_code, detail=detail)
            if status == "contract_error" or status_code == 422:
                raise ContractViolation(str(reason or "contract violation"), status_code=status_code, detail=detail)
            if status_code >= 500:
                raise RuntimeUnavailable(str(reason or "runtime unavailable"), status_code=status_code, detail=detail)
            if status == "failed" and "provider_results" not in payload:
                raise ProviderRuntimeClientError(str(reason or "runtime failed"), status_code=status_code, detail=detail)
        '''
    ).lstrip()


def _render_client(product: Dict[str, Any], action_schemas: Dict[str, Any]) -> str:
    product_id = product["id"]
    client_cls = class_name_from_id(product_id, "Client")
    imports = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict, List",
        "",
        "from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient",
        "from .models import (",
        "    ProviderBinding,",
    ]
    model_names: List[str] = []
    for action_id in action_schemas:
        model_names.append(class_name_from_id(action_id, "Input"))
        model_names.append(class_name_from_id(action_id, "Result"))
        model_names.append(class_name_from_id(action_id, "ProviderResult"))
        model_names.append(class_name_from_id(action_id, "MultiProviderResult"))
    imports.extend(f"    {name}," for name in model_names)
    imports.append(")")
    imports.append("")
    imports.append("")
    blocks = imports
    blocks.append(f"class {client_cls}:")
    blocks.append("    def __init__(self, runtime: ProviderRuntimeClient | AsyncProviderRuntimeClient) -> None:")
    blocks.append("        self.runtime = runtime")
    blocks.append("")
    for action_id, action in action_schemas.items():
        input_cls = class_name_from_id(action_id, "Input")
        multi_result_cls = class_name_from_id(action_id, "MultiProviderResult")
        params = ["providers: List[ProviderBinding]"]
        for name, spec in _business_inputs(action):
            default = "" if _is_required(spec) else f" = {_default_code(spec)}"
            params.append(f"{name}: {_py_type(spec.get('type', 'object'))}{default}")
        signature = ", ".join(["self", "*", *params])
        blocks.append(f"    def {action_id}({signature}) -> {multi_result_cls}:")
        blocks.extend(_docstring_lines(action))
        blocks.extend(
            _method_body(
                product,
                action_id,
                action,
                input_cls,
                multi_result_cls,
                async_mode=False,
            )
        )
        blocks.append("")
        blocks.append(f"    async def a{action_id}({signature}) -> {multi_result_cls}:")
        blocks.extend(_docstring_lines(action))
        blocks.extend(
            _method_body(
                product,
                action_id,
                action,
                input_cls,
                multi_result_cls,
                async_mode=True,
            )
        )
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def _docstring_lines(action: Dict[str, Any]) -> List[str]:
    lines = ['        """' + action.get("description", "Execute product action.")]
    depends_on = action.get("depends_on", [])
    if depends_on:
        lines.append("")
        lines.append("        Internal ontology dependencies used by Provider Runtime:")
        lines.extend(f"        - {field}" for field in depends_on)
        lines.append("")
        lines.append("        These dependencies are not external parameters; the Runtime resolves them through provider mappings.")
    lines.append('        """')
    return lines


def _method_body(
    product: Dict[str, Any],
    action_id: str,
    action: Dict[str, Any],
    input_cls: str,
    multi_result_cls: str,
    *,
    async_mode: bool,
) -> List[str]:
    arg_names = [name for name, _ in _business_inputs(action)]
    model_args = ", ".join(f"{name}={name}" for name in arg_names)
    maybe_await = "await " if async_mode else ""
    return [
        f"        request = {input_cls}({model_args})",
        "        payload = request.model_dump(exclude_none=True)",
        "        provider_values = [",
        "            ProviderBinding.model_validate(item).model_dump() for item in providers",
        "        ]",
        f"        response = {maybe_await}self.runtime.execute_action(",
        f"            product_id={product['id']!r},",
        f"            action_id={action_id!r},",
        "            providers=provider_values,",
        f"            purpose={product['purpose']!r},",
        f"            product_version={product['id'] + '@' + product['version']!r},",
        "            payload=payload,",
        "        )",
        f"        return {multi_result_cls}.model_validate(response)",
    ]


def _render_init(product: Dict[str, Any], action_schemas: Dict[str, Any]) -> str:
    client_cls = class_name_from_id(product["id"], "Client")
    names = [
        client_cls,
        "ProviderBinding",
        "ProviderRuntimeClient",
        "AsyncProviderRuntimeClient",
    ]
    lines = [
        f"from .client import {client_cls}",
        "from .runtime import AsyncProviderRuntimeClient, ProviderRuntimeClient",
        "from .models import (",
        "    ProviderBinding,",
    ]
    for action_id in action_schemas:
        for suffix in ("Input", "Result", "ProviderResult", "MultiProviderResult"):
            model_name = class_name_from_id(action_id, suffix)
            lines.append(f"    {model_name},")
            names.append(model_name)
    lines.append(")")
    lines.append("")
    lines.append(f"__all__ = {names!r}")
    return "\n".join(lines) + "\n"


def _render_readme(product: Dict[str, Any], action_schemas: Dict[str, Any]) -> str:
    pkg = package_name(product["id"])
    client_cls = class_name_from_id(product["id"], "Client")
    first_action = next(iter(action_schemas))
    action = action_schemas[first_action]
    if product["id"] == "changchun-excavation-risk":
        api_key = "demo_key_construction_agent"
        requester_agent = "agent:construction-safety"
        provider_lines = [
            '    ProviderBinding(provider_id="changchun", entitlement_id="ent_changchun"),'
        ]
    else:
        api_key = "demo_key_bank_agent"
        requester_agent = "agent:bank-risk"
        provider_lines = [
            '    ProviderBinding(provider_id="grid", entitlement_id="ent_grid"),',
            '    ProviderBinding(provider_id="integrated-energy", entitlement_id="ent_energy"),',
        ]
    sample_args = ["    providers=providers,"]
    for name, spec in _business_inputs(action):
        if spec.get("type") == "string":
            sample_args.append(f'    {name}="demo",')
        elif spec.get("type") == "integer":
            sample_args.append(f"    {name}={spec.get('default', 1)},")
        elif spec.get("type") == "number":
            sample_args.append(f"    {name}=1.0,")
        else:
            sample_args.append(f"    {name}={{}},")
    args = "\n".join(sample_args)
    providers = "\n".join(provider_lines)
    return (
        f"# {product['id']} Product OSDK\n\n"
        "Generated from DOIR action schema. The SDK is a remote workload client: "
        "it calls a trusted gateway, not a database or internal Runtime object.\n\n"
        "```python\n"
        f"from {pkg} import {client_cls}, ProviderBinding, ProviderRuntimeClient\n\n"
        "runtime = ProviderRuntimeClient(\n"
        "    base_url=\"http://127.0.0.1:8000\",\n"
        f"    api_key=\"{api_key}\",\n"
        f"    requester_agent=\"{requester_agent}\",\n"
        ")\n"
        f"client = {client_cls}(runtime=runtime)\n"
        "providers = [\n"
        f"{providers}\n"
        "]\n"
        f"result = client.{first_action}(\n"
        f"{args}\n"
        ")\n"
        "for provider_id, provider_result in result.provider_results.items():\n"
        "    print(provider_id, provider_result.status, provider_result.receipt_id)\n"
        "```\n"
    )


def _render_pyproject(product: Dict[str, Any]) -> str:
    pkg = package_name(product["id"])
    return textwrap.dedent(
        f"""
        [build-system]
        requires = ["setuptools>=68"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{pkg}"
        version = "{product['version']}"
        description = "Generated Product OSDK for {product['id']}"
        requires-python = ">=3.10"
        dependencies = ["pydantic>=2.7"]

        [tool.setuptools.packages.find]
        where = ["."]
        """
    ).lstrip()


def generate_python_sdk_files(
    product: Dict[str, Any],
    action_schemas: Dict[str, Any],
    output_schema: Dict[str, Any],
) -> Dict[str, str]:
    pkg = package_name(product["id"])
    return {
        "pyproject.toml": _render_pyproject(product),
        "README.md": _render_readme(product, action_schemas),
        f"{pkg}/__init__.py": _render_init(product, action_schemas),
        f"{pkg}/client.py": _render_client(product, action_schemas),
        f"{pkg}/models.py": _render_models(product, action_schemas, output_schema),
        f"{pkg}/runtime.py": _render_runtime(),
        f"{pkg}/errors.py": _render_errors(),
    }


def python_osdk_preview(
    product: Dict[str, Any],
    action_schemas: Dict[str, Any],
    output_schema: Dict[str, Any],
) -> str:
    files = generate_python_sdk_files(product, action_schemas, output_schema)
    pkg = package_name(product["id"])
    sections = [
        "# Generated Product OSDK preview",
        f"# package: {pkg}",
        "",
        "# --- client.py ---",
        files[f"{pkg}/client.py"],
        "# --- models.py ---",
        files[f"{pkg}/models.py"],
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_python_sdk_package(base_dir: Path, product: Dict[str, Any], files: Dict[str, str]) -> Path:
    package_dir = base_dir / package_name(product["id"])
    package_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, content in files.items():
        path = package_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return package_dir
