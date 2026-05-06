
&lt;!---
SKILL.md entry: [06_security_checklist.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/06_security_checklist.md)
Category: 6. Security Audit Checklist
When to use: When conducting security audits
---&gt;

# Security Audit Checklist

> Focus on high-impact controls only. If any P0 appears, block merge.

## P0 Blockers

- [ ] Hardcoded secrets/tokens/credentials
- [ ] SQL/Command/Template injection risk
- [ ] Missing auth/authz on privileged endpoints
- [ ] IDOR/BOLA (object-level authorization broken)
- [ ] Untrusted deserialization / unsafe eval
- [ ] Known exploited CVE without mitigation

## Core Controls

### Identity & Access
- [ ] Server-side authorization for every sensitive operation
- [ ] Least privilege for users, service accounts, IAM roles
- [ ] Session/token lifecycle includes expiry and revocation

### Data & Secrets
- [ ] Secrets from vault/env only; never in repo or image layers
- [ ] PII masked in logs and prompts
- [ ] Encryption in transit and at rest for sensitive data

### Input / Output Security
- [ ] Strict input validation and parameterized queries
- [ ] XSS-safe rendering and secure headers
- [ ] Error responses avoid stack/path leakage

### Supply Chain
- [ ] Dependency and container scans in CI
- [ ] Lockfiles and provenance checks enabled
- [ ] Secret scanning in pre-commit and CI

## AI / Agent Specific

- [ ] Prompt injection detection and policy boundary enforcement
- [ ] Tool calling permission model (allowlist + approval gate)
- [ ] Retrieval access control (tenant/user scoped)
- [ ] Prompt/output logs are privacy-safe and auditable
- [ ] Budget and abuse controls (rate limits, token caps)
