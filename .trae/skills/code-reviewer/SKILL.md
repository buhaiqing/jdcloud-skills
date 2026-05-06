---
name: "code-reviewer"
description: "Production-grade code review skill for Python, Go, JavaScript/TypeScript, Java/Kotlin, Rust, infrastructure, and AI Agent/RAG skill systems. Focuses on high-value findings in correctness, security, reliability, and maintainability."
---

# Code Reviewer

Unified code review skill designed to identify the highest business risks with minimal cognitive overhead and provide actionable remediation guidance.

## Review Principles (High-Value Only)

1. **Risk-first**: prioritize issues that can cause incidents, data leaks, or incorrect decisions.
2. **Evidence-first**: every finding must be traceable, reproducible, and fixable.
3. **Minimal output**: include only must-fix items and high-leverage improvements; avoid procedural noise.
4. **Multi-pass self-check**: run at least two review passes to reduce false negatives and false positives.

## Trigger Conditions

- The user requests code, PR, or pre-release quality review.
- The user requests a focused audit on security, performance, or maintainability.
- The user requests review of AI Agent, RAG, or Skill systems.

## Core Workflow (MVR: Minimum Viable Review)

1. **Rapid scoping (5 min)**: identify language, change scope, and business-critical paths.
2. **P0/P1 scan (15-30 min)**: focus on correctness, security, and reliability.
3. **High-value optimization (10-20 min)**: target performance, maintainability, and test gaps.
4. **Two-pass reflection (10 min)**:
   - Pass 1: verify that no high-risk issue was missed.
   - Pass 2: verify recommendations are actionable and not over-engineered.
5. **Structured output**: provide conclusions and action items by severity.

## Review Dimensions (Condensed)

- **Correctness**: business logic accuracy, edge-case handling, error behavior.
- **Security**: authentication/authorization, input/output hardening, secret and dependency security.
- **Reliability**: timeout/retry policies, graceful degradation/circuit breaking, recoverability.
- **Maintainability**: complexity control, duplication, test quality.
- **AI/Agent**: prompt injection defense, tool permission boundaries, RAG faithfulness, memory/state management, prompt engineering quality, observability and cost control.
- **AI/Agent Composition**: Skill combination privilege escalation, context leakage, cascade failure isolation, resource contention.
- **AI/Agent Adversarial**: red team testing, side-channel leakage, social engineering resistance.

## Merge-blocking Conditions (Hard Stop)

- Hardcoded secrets or credentials.
- Injection-class vulnerabilities (SQL/Command/Prompt Injection).
- Privileged endpoints without authentication/authorization, or any privilege escalation path.
- Changes that can cause data corruption or unrecoverable failures.
- Known high-risk vulnerable dependencies without mitigation.
- Skill combination producing privilege escalation beyond individual permission union.
- Context leakage across tenants/users in Skill composition.
- Cascade failure without isolation in chained Skill calls.

## Frontier Focus (High-Value 2026)

- **Agentic Security**: tool-call allowlists, parameter validation, and human approval gates.
- **RAG Reliability**: enforce retrieval/generation metrics (Recall@k, Faithfulness) as release gates.
- **LLM Cost Governance**: token budgets, cache hit rate targets, and fallback model strategy.
- **Observability Standardization**: unified telemetry for trace, cost, and safety events.
- **Nondeterministic Evaluation**: statistical significance, risk-adjusted scoring, confidence intervals for LLM-driven systems.
- **Adversarial Testing**: red team review as mandatory pre-release gate, prompt injection fuzz testing.
- **Skill Lifecycle Governance**: runtime drift detection, post-incident review, decommissioning standards.
- **Memory & State Safety**: context window truncation, memory poisoning defense, state corruption recovery.

## Reference Index

- Language guides: `references/01_python_guide.md` `references/02_go_guide.md` `references/03_js_ts_guide.md` `references/04_java_kotlin_guide.md` `references/08_rust_guide.md` `references/09_infra_guide.md`
- General framework: `references/05_general_framework.md`
- Security checklist: `references/06_security_checklist.md`
- Report template: `references/07_report_template.md`
- AI Agent / RAG: `references/10_ai_agent_rag_guide.md`
- Agent Skill specialization: `references/11_agent_skill_review_system.md`
- Cross-language blocker index: `references/12_cross_language_blockers.md`
- One-page PR execution checklist: `references/13_pr_review_one_page_checklist.md`
- Nondeterministic evaluation: `references/14_nondeterministic_eval_guide.md`
- Adversarial / red team review: `references/15_adversarial_review_guide.md`
- Skill lifecycle review: `references/16_skill_lifecycle_review.md`
