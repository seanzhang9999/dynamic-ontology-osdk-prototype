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
