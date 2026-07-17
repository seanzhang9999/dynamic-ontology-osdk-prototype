# Acceptance Checklist

- [ ] API `/health` returns `{"status":"ok"}`.
- [ ] `make test` passes all compiler, policy, runtime, and receipt tests.
- [ ] `npm run build` succeeds in `ui/demo-console`.
- [ ] Demo Console loads product manifests from `/demo/state`.
- [ ] Running enterprise credit creates two successful jobs, one for `grid` and one for `integrated-energy`.
- [ ] Enterprise credit result does not contain `raw_monthly_kwh`, `kwh`, source row IDs, or ledger rows.
- [ ] Revoked entitlement denies execution with `entitlement_revoked`.
- [ ] Running Changchun risk returns only risk summary fields, no exact coordinates or segment IDs.
- [ ] Coordinate-core recompile changes Changchun product version to `1.1.0`.
- [ ] Receipt verification passes for untouched receipts and fails after tampering.
- [ ] Double-scenario demo can be completed in 8-10 minutes.

## Split Gateway / Provider Runtime

- [ ] Gateway `/health` lists logical Provider IDs but contains no Provider dataset.
- [ ] Grid, integrated-energy, and Changchun Runtime health endpoints report their immutable Provider IDs.
- [ ] A generated Product OSDK request with two `ProviderBinding` values returns two `succeeded` Provider results and two signed Receipts.
- [ ] The fan-out response contains no bank-owned aggregate credit score or Provider weighting.
- [ ] Revoking one Provider Entitlement produces `partial`; the revoked Provider is not dispatched and the other result remains available.
- [ ] Stopping one Provider Runtime produces `partial` with `provider_unavailable`; other Provider results remain available.
- [ ] A Provider Runtime rejects missing internal Gateway credentials and a mismatched `provider_id`.
- [ ] Each Provider Runtime loads only its own configured fixture dataset.
- [ ] The split-backend demonstration is described as synthetic-data execution, not as completed production-source isolation.

