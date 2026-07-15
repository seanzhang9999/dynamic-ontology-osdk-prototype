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

