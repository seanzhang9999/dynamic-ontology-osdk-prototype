# Gateway and Provider Runtime Fan-out Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the trusted Gateway from provider-owned Runtime processes and generate an OSDK that makes one typed multi-provider request while leaving aggregation to the bank.

**Architecture:** A control-plane-only Gateway validates one product action and a list of provider entitlement bindings, then dispatches independent HTTP calls through a private provider route table. Each Provider Runtime is fixed to one provider identity, executes locally, signs its own receipt, and returns a single-provider job; Gateway only correlates these responses.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, standard-library `urllib` and `concurrent.futures`, generated Python packages, unittest, Docker Compose.

---

### Task 1: Define fan-out contracts and tests

**Files:**
- Modify: `core/trusted_data_demo/models.py`
- Modify: `tests/test_gateway.py`

**Steps:**

1. Add tests for a two-provider request, duplicate providers, one denied entitlement and one unavailable provider.
2. Run `\.venv\Scripts\python -m unittest tests.test_gateway` and confirm the new tests fail.
3. Add internal provider binding/result models only where they reduce validation ambiguity.

### Task 2: Add Gateway control plane and provider transport

**Files:**
- Create: `core/trusted_data_demo/control_plane.py`
- Modify: `core/trusted_data_demo/gateway.py`
- Create: `core/trusted_data_demo/gateway_app.py`
- Test: `tests/test_gateway.py`

**Steps:**

1. Extract product catalog, entitlement issuance and application identity construction into a control plane that does not load provider data.
2. Define injectable in-process and HTTP Provider transports.
3. Normalize legacy single-provider and new `providers` envelopes.
4. Preflight each entitlement, dispatch allowed providers concurrently and return `completed`, `partial` or `failed` with per-provider results.
5. Run Gateway tests and confirm single-provider compatibility plus fan-out behavior.

### Task 3: Add provider-scoped Runtime service

**Files:**
- Modify: `core/trusted_data_demo/runtime.py`
- Create: `core/trusted_data_demo/provider_app.py`
- Create: `tests/test_provider_app.py`

**Steps:**

1. Make `TrustedDataDemo` optionally load only one Provider dataset.
2. Allow a Provider Runtime to execute with the Gateway's already-allowed policy decision while preserving direct local policy tests.
3. Add `/internal/actions/execute`, internal-key authentication, provider-identity checks and action dispatch.
4. Test missing internal credentials, provider mismatch and successful local execution with a signed receipt.

### Task 4: Generate typed multi-provider OSDK

**Files:**
- Modify: `core/trusted_data_demo/osdk_generator.py`
- Modify: `tests/test_compiler.py`
- Regenerate: `generated/python/enterprise_energy_credit/`
- Regenerate: `generated/python/changchun_excavation_risk/`

**Steps:**

1. Generate `ProviderBinding`, per-provider action results and a multi-provider result model.
2. Generate action methods that accept `providers` plus business payload fields; remove provider URL knowledge from the product client.
3. Keep the runtime HTTP client focused on Gateway `/actions/execute`.
4. Regenerate packages and verify both packages import.

### Task 5: Deploy and verify independent processes

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Modify: `docs/project-status-and-osdk.md`
- Create: `tests/test_remote_fanout_e2e.py` if a stable subprocess test is practical; otherwise record the manual smoke command.

**Steps:**

1. Run Gateway and two power-credit Provider Runtimes on separate ports.
2. Issue one entitlement for each provider through Gateway.
3. Use the generated OSDK to make one fan-out call and verify two distinct runtime versions and receipts.
4. Stop one Runtime and verify a `partial` response retains the successful Provider result.
5. Run all Python tests, regenerate SDK packages, build the frontend and run `git diff --check`.
