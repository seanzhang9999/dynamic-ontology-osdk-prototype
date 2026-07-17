# ADR-0001: Separate Gateway Fan-out From Provider Runtime Execution

## Status

Accepted

## Context

The current remote OSDK sends an action envelope to `SimpleTrustedGateway`, but the Gateway invokes `TrustedDataDemo` in the same process. That validates the product contract but does not validate a provider-owned execution boundary. The enterprise-credit scenario also needs one bank request to reach multiple providers without making the bank application discover provider URLs.

Functional requirements:

- One OSDK action may name multiple logical providers and one entitlement per provider.
- Gateway authenticates the bank workload, validates the product contract and each entitlement, then fans out concurrently.
- Each Provider Runtime owns one provider identity and its local data only.
- Gateway returns per-provider results, failures and signed receipts without calculating the bank's combined score.
- The generated OSDK exposes typed provider bindings and typed per-provider results.

Prototype non-functional requirements:

- Provider calls have bounded timeouts and isolated failures.
- Unknown and duplicate provider IDs are rejected before dispatch.
- A Provider Runtime rejects application traffic that does not carry the internal Gateway credential.
- Existing single-provider envelopes remain supported during migration.
- No message broker, service mesh or Kubernetes dependency is introduced at this stage.

## Decision

Use a small synchronous service topology with one public Gateway process and one FastAPI process per Provider Runtime.

```text
Bank application -> Generated Product OSDK -> Gateway
                                              |-> grid Runtime
                                              |-> integrated-energy Runtime
                                              `-> changchun Runtime
```

The OSDK sends a shared business payload plus `providers: [{provider_id, entitlement_id}]`. Gateway resolves runtime URLs from its private route table, performs entitlement preflight, consumes an allowed entitlement before dispatch, and sends a trusted internal action envelope to each Runtime. Fan-out uses a bounded thread pool because the current stack uses synchronous FastAPI and standard-library HTTP clients.

Each Runtime is configured with one immutable `DEMO_PROVIDER_ID`. It validates the internal Gateway key and provider match, executes only the registered product action, and signs its own receipt. The Gateway returns `provider_results` and a batch status of `completed`, `partial` or `failed`. The bank owns all cross-provider weighting, scoring and minimum-source rules.

## Consequences

### Positive

- The prototype demonstrates an actual network and process boundary between routing and data execution.
- Provider URLs and topology remain hidden from the OSDK and bank application.
- Per-provider receipts preserve provenance and partial failures remain visible.
- Gateway stays product-agnostic and does not accumulate domain scoring logic.

### Negative

- Network timeouts and partial results become part of the public response contract.
- Prototype service authentication still uses a shared development key rather than mTLS or workload identity.
- Policy consumption occurs before remote execution, so a transport failure can consume a call. Production will need idempotency and reservation semantics.

### Neutral

- Registry, Policy and route configuration remain in the Gateway process for this iteration.
- Provider datasets remain synthetic, although each Runtime is process-scoped to one provider. Real SQL/GIS adapters remain a separate milestone.

## Alternatives Considered

**Client-side fan-out** was rejected because it exposes provider orchestration to every bank application and weakens central routing and policy enforcement.

**Gateway business aggregation** was rejected because credit weighting belongs to the bank and would couple infrastructure to product-specific algorithms.

**A separate Product Orchestrator** remains appropriate when a future cross-provider aggregation algorithm is itself a governed product, but is unnecessary for the current bank-owned model.

**A message broker or service mesh** was deferred because it adds operational complexity without improving the current prototype's core validation.

## Failure Modes

| Failure | Behavior | Mitigation |
| --- | --- | --- |
| Unknown Provider | Request rejected before fan-out | Gateway route-table validation |
| Invalid/revoked entitlement | Provider result marked `denied`; no Runtime call | Per-provider policy preflight |
| Runtime timeout/unavailable | Provider result marked `failed`; other calls continue | Bounded timeout and isolated futures |
| Provider mismatch | Runtime returns contract error | Immutable Runtime provider identity |
| Some providers fail | Batch status is `partial` | Bank decides whether enough sources succeeded |
| All providers fail | Batch status is `failed` | No aggregate is produced by infrastructure |

