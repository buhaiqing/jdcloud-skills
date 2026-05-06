<!---
SKILL.md entry: [07_report_template.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/07_report_template.md)
Category: 7. Report Template
When to use: When outputting code review reports
--->

# Code Review Report Template (Lean)

> Project: [name]  
> Scope: [files/modules]  
> Reviewer: [name]  
> Date: [yyyy-mm-dd]

## Decision

- **Result**: [Approve | Request Changes | Block]
- **Reason**: [one sentence]
- **Must Fix Before Merge**: [count of P0/P1]

## Findings (By Severity)

### P0/P1 (Blocking)

1. **[Title]**
   - Location: `[path]`
   - Risk: [what can break or leak]
   - Fix: [concrete action]
   - Evidence: [test/log/repro note]

### P2 (Important)

1. **[Title]**
   - Location: `[path]`
   - Risk: [impact]
   - Fix: [concrete action]

### P3 (Nice to Have)

1. **[Title]**
   - Location: `[path]`
   - Suggestion: [optional improvement]

## Verification

- Checks run: `[lint] [tests] [security scan]`
- Regression risk: [High/Medium/Low]
- Confidence: [High/Medium/Low]

## Top 3 Next Actions

1. [Action]
2. [Action]
3. [Action]
