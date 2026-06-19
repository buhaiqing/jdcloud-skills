# Failure Patterns — jdcloud-skill-generator

> Cross-session failure memory for the GCL Reflexion integration.
> This file is loaded lazily during GCL Pre-flight (step [0]) to inject
> known failure patterns as prevention hints for the Generator.

## §1 CLI Parameter Errors

### Pattern: InvalidSkillName
- **Category**: cli_parameter
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill with invalid name
- **Error**: `InvalidParameter: InvalidSkillName`
- **Fix**: Skill name must follow naming convention (jdcloud-<product>-ops)
- **Count**: 1
- **Reusable**: true

### Pattern: MissingRequiredMetadata
- **Category**: cli_parameter
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing required metadata fields)
- **Error**: `MissingParameter: required metadata fields missing`
- **Fix**: Always include name, description, license, compatibility, metadata
- **Count**: 1
- **Reusable**: true

## §2 Skill Generation Errors

### Pattern: MissingYAMLFrontmatter
- **Category**: skill_generation
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing YAML frontmatter)
- **Error**: SKILL.md missing `---` block
- **Fix**: Always start with `---` block containing name, description, license, compatibility, metadata
- **Count**: 1
- **Reusable**: true

### Pattern: MissingTriggerScope
- **Category**: skill_generation
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing SHOULD/SHOULD NOT section)
- **Error**: SKILL.md missing trigger conditions
- **Fix**: Add trigger conditions chapter with delegation rules
- **Count**: 1
- **Reusable**: true

### Pattern: BrokenRelativeLinks
- **Category**: skill_generation
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (broken relative links)
- **Error**: Links to references/ files broken
- **Fix**: Use `../` prefix for advanced/ → references/ links
- **Count**: 1
- **Reusable**: true

### Pattern: MissingGCLQualityGate
- **Category**: skill_generation
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing GCL Quality Gate section)
- **Error**: SKILL.md missing Quality Gate section
- **Fix**: Add `## Quality Gate (GCL)` with rubric reference and parameters
- **Count**: 1
- **Reusable**: true

### Pattern: MissingWellArchitectedTable
- **Category**: skill_generation
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing Well-Architected table)
- **Error**: SKILL.md missing Well-Architected table
- **Fix**: Add five-pillar table (Security, Stability, Cost, Efficiency, Performance)
- **Count**: 1
- **Reusable**: true

## §3 Cross-Skill Integration Errors

### Pattern: DelegationRuleMissing
- **Category**: cross_skill
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (missing delegation rules)
- **Error**: SKILL.md missing delegation rules to other skills
- **Fix**: Add delegation rules for cross-skill operations
- **Count**: 1
- **Reusable**: true

### Pattern: InconsistentVariableConvention
- **Category**: cross_skill
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (inconsistent variable convention)
- **Error**: Variable convention inconsistent with other skills
- **Fix**: Follow repository-wide variable convention ({{env.*}}, {{user.*}}, {{output.*}})
- **Count**: 1
- **Reusable**: true

## §4 Runtime Errors

### Pattern: ThrottlingRateLimit
- **Category**: runtime
- **Skill**: jdcloud-skill-generator
- **Command**: Any generation operation
- **Error**: `Throttling: Rate limit exceeded (HTTP 429)`
- **Fix**: Retry with exponential backoff; reduce request frequency
- **Count**: 1
- **Reusable**: true

### Pattern: InternalServerError
- **Category**: runtime
- **Skill**: jdcloud-skill-generator
- **Command**: Any generation operation
- **Error**: `InternalError: Server error (HTTP 500)`
- **Fix**: Retry with backoff; contact support if persistent
- **Count**: 1
- **Reusable**: true

### Pattern: CredentialMisconfigured
- **Category**: runtime
- **Skill**: jdcloud-skill-generator
- **Command**: Any generation operation
- **Error**: `Unauthorized: Invalid credentials`
- **Fix**: Verify `~/.jdc/config` has correct access_key and secret_key
- **Count**: 1
- **Reusable**: true

## §5 Token Efficiency Warnings

### Pattern: LargeSkillDefinition
- **Category**: token_efficiency
- **Skill**: jdcloud-skill-generator
- **Command**: Generate skill (large SKILL.md)
- **Warning**: SKILL.md too large, consumes excessive tokens
- **Fix**: Keep SKILL.md concise; move detailed content to references/
- **Count**: 1
- **Reusable**: true

## Pattern Extraction Format

When a GCL iteration fails, extract failure pattern using this format:

```json
{
  "category": "cli_parameter|skill_generation|cross_skill|runtime|token_efficiency",
  "skill": "jdcloud-skill-generator",
  "command": "exact generation operation",
  "error": "error message or code",
  "fix": "specific fix or remediation step",
  "reusable": true
}
```

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-19 | Initial failure patterns for `jdcloud-skill-generator` |
