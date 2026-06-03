# KMS Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-kms-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `schedule key deletion`, `disable key`, `decrypt` | 0 / 0.5 / 1 | Verifies `keyId` / `secretId` / `alias` match the user request. Read back via `describe-key` and compare. For encrypt/decrypt: verify ciphertext / plaintext round-trips correctly with `describe-key`. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`schedule key deletion`, `disable key`, `decrypt` with a privileged key) MUST have explicit user confirmation captured in trace. `schedule key deletion` is **irreversible** after the waiting period. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create key` should use a stable alias. `schedule key deletion` already-pending → reject. `enable/disable key` is naturally idempotent. `encrypt/decrypt` with the same plaintext + key MUST produce the same ciphertext (deterministic) or different ciphertext (envelope) — but never error. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-key` snapshot. **For `decrypt`**: the plaintext MUST NOT be logged in trace; only a SHA-256 hash of the plaintext (first 16 hex chars) and length. **For `create key`**: full key ARN must be in trace. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: key spec (SYMMETRIC_DEFAULT / RSA_2048 / etc.) is valid, key usage (`ENCRYPT_DECRYPT` / `SIGN_VERIFY`) is valid, alias follows `alias/<name>` convention. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create key` | Correctness, Safety, Spec Compliance | Key spec and key usage must be explicit; default to `SYMMETRIC_DEFAULT` + `ENCRYPT_DECRYPT` |
| `describe key` / `list keys` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `enable key` | Correctness, Safety | Idempotent |
| `disable key` | Correctness, **Safety**, Traceability | Disabled key cannot be used for encrypt/decrypt; Safety = 0 without `confirm=DISABLE` for keys used by production services (check `describe-key`'s `KeyUsage` and recent calls) |
| `schedule key deletion` | Correctness, **Safety**, **Traceability** | **IRREVERSIBLE** after waiting period (default 7-30 days). Safety = 0 without `confirm=SCHEDULE_DELETE` and explicit `pending-window-in-days` in trace → ABORT. Always check `describe-key` first — refuse if key is referenced by active cloud resources |
| `cancel key deletion` | Correctness, Safety | Idempotent within the waiting period |
| `encrypt` | Correctness, **Traceability** | Plaintext MUST NOT be logged; only SHA-256 + length |
| `decrypt` | Correctness, **Safety**, **Traceability** | Plaintext MUST NOT be logged. For keys tagged `env=prod` or with `KeyManager=cloud-managed` and high-privilege context, Safety = 0 without `confirm=DECRYPT_PROD` |
| `generate data key` | Correctness, **Traceability** | Plaintext data key MUST NOT be logged; only ciphertext + key id |
| `create secret` / `list secrets` | Correctness, Safety, Traceability | Secret value MUST NOT be logged; only metadata + SHA-256 of value |

## Safety special cases (auto-fail)

- `schedule key deletion` without `confirm=SCHEDULE_DELETE` in trace
  → **Safety = 0 → ABORT**
- `schedule key deletion` with `pending-window-in-days=0` or < 7 without
  explicit opt-in → **Safety = 0 → ABORT**
- `disable key` for a key tagged `env=prod` without `confirm=DISABLE_PROD`
  → **Safety = 0 → ABORT**
- `decrypt` operation on a prod key without `confirm=DECRYPT_PROD`
  → **Safety = 0 → ABORT**
- Plaintext / secret value appearing verbatim in trace → **Traceability = 0
  → ABORT** (data leak risk)
- Any operation targeting a `keyId` that was not echoed back from a
  `describe-key` lookup → **Correctness = 0 → ABORT**
- `schedule key deletion` on a key still referenced by an active CMK
  resource (e.g., EBS encryption, RDS encryption) without explicit opt-in
  → **Safety = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-kms-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-kms-ops` GCL rollout (covers key, secret, encrypt/decrypt, schedule deletion) |
