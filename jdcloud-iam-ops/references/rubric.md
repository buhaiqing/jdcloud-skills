# IAM Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-iam-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete sub-user`, `attach policy`, `create access-key` | 0 / 0.5 / 1 | Verifies `subUserName` / `groupName` / `roleName` / `policyName` / `accessKeyId` match the user request. Read back via `describe-sub-user` / `describe-group` / `describe-policy` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Privileged ops (`create access-key`, `attach policy` with `AdministratorAccess` or `*:*`, `assume role` with elevated privilege, any op on the main account) MUST have explicit user confirmation captured in trace. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `attach policy` is naturally idempotent. `create sub-user` / `create group` / `create role` should use a stable name; re-creation of the same name MUST be guarded. `create access-key` returns 2 keys max — must check existing keys first. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-*` snapshot. Score 1 only if all four present. **For `create access-key`**: full access-key id and creation timestamp MUST be in trace; the secret value MUST NOT be logged. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: policy name follows `Service-Resource-Action` convention, role trust policy is well-formed JSON, group naming convention. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create sub-user` | Correctness, Safety | Display name + login password policy; check duplicates first |
| `create group` | Correctness, Safety | Idempotent check via list |
| `create role` | Correctness, Safety | Trust policy JSON must appear in trace; **never** trust `*` as principal without user opt-in |
| `create policy` | Correctness, Safety, Spec Compliance | Policy document JSON must appear in trace; reject `Effect: Allow, Action: *, Resource: *` without explicit opt-in |
| `attach policy` (sub-user/group/role) | Correctness, **Safety**, Spec Compliance | If policy is `AdministratorAccess` or contains `Action: *` + `Resource: *` → Safety = 0 without explicit `confirm=ATTACH_ADMIN` → ABORT |
| `create access-key` (main account) | Correctness, **Safety**, Traceability | Safety = 0 without explicit `confirm=CREATE_KEY`; main account key is the highest-privilege credential. Check existing keys count first (max 2); if already 2, refuse without rotation plan |
| `delete sub-user` | Correctness, **Safety**, Traceability | MUST detach all policies and remove from all groups **before** deletion; missing either → Safety = 0. Must include pre-delete snapshot of attached policies + group memberships |
| `assume role` (STS) | Correctness, **Safety**, Traceability | Session duration MUST be ≤ 1 hour by default; longer requires `confirm=EXTEND_SESSION`. Role ARN must be verified against the target role's trust policy |
| `describe sub-user` / `list` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |

## Safety special cases (auto-fail)

- `create access-key` for the main account without `confirm=CREATE_KEY` in
  trace → **Safety = 0 → ABORT**
- `attach policy` of `AdministratorAccess` or wildcard `*:*` without
  `confirm=ATTACH_ADMIN` in trace → **Safety = 0 → ABORT**
- `delete sub-user` who still has attached policies or group memberships
  → **Safety = 0 → ABORT** (must detach / remove first)
- `assume role` with session duration > 1 hour without `confirm=EXTEND_SESSION`
  → **Safety = 0 → ABORT**
- Any operation targeting a sub-user / group / role / policy that was not
  echoed back from a `describe-*` lookup → **Correctness = 0 → ABORT**
- Trust policy containing `"Principal": "*"` without explicit opt-in
  → **Safety = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-iam-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-iam-ops` GCL rollout (covers sub-user, group, role, policy, access-key, STS) |
