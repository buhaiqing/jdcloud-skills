#!/usr/bin/env bash
# validate_skill.sh — Verifiable knowledge asset for jdcloud-clb-ops
# Usage: bash scripts/validate_skill.sh
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_ROOT"

errors=0
echo "=== jdcloud-clb-ops Skill Validation ==="
echo ""

# ---- Check 1: Internal link validity ----
echo "--- Check 1: Internal links in SKILL.md ---"
while IFS= read -r link; do
  # Skip external links (http/https) and anchor-only links
  if echo "$link" | grep -qE '^https?://' || echo "$link" | grep -qE '^#'; then
    continue
  fi
  # Remove anchor suffix
  target="${link%%#*}"
  if [[ ! -f "$SKILL_ROOT/$target" ]]; then
    echo "  BROKEN: $link → $target (not found)"
    ((errors++))
  fi
done < <(grep -oE '\]\([^)]+\)' "$SKILL_ROOT/SKILL.md" | sed 's/.*\](//;s/)$//' | grep '\.md$')

echo "  OK"
echo ""

# ---- Check 2: Reference files existence ----
echo "--- Check 2: Reference files ---"
expected_refs=(
  "references/cli-usage.md"
  "references/api-sdk-usage.md"
  "references/core-concepts.md"
  "references/integration.md"
  "references/monitoring.md"
  "references/prompt-templates.md"
  "references/rubric.md"
  "references/troubleshooting.md"
)
for ref in "${expected_refs[@]}"; do
  if [[ ! -f "$SKILL_ROOT/$ref" ]]; then
    echo "  MISSING: $ref"
    ((errors++))
  fi
done
echo "  OK (${#expected_refs[@]} files)"
echo ""

# ---- Check 3: No legacy parameter names ----
echo "--- Check 3: Legacy parameter names ---"
banned=("listener-ports" "listenerPorts")
for pattern in "${banned[@]}"; do
  matches=$(grep -rl "$pattern" "$SKILL_ROOT" --include="*.md" --include="*.yaml" 2>/dev/null || true)
  if [[ -n "$matches" ]]; then
    echo "  FOUND '$pattern' in:"
    echo "$matches" | sed 's/^/    /'
    ((errors++))
  fi
done
echo "  OK"
echo ""

# ---- Check 4: rubric_version consistency ----
echo "--- Check 4: rubric_version consistency ---"
rubric_label=$(grep -oE 'Rubric version.*`v[0-9]+`' "$SKILL_ROOT/references/rubric.md" | grep -oE 'v[0-9]+' | head -1 || echo "NOT_FOUND")
skill_label=$(grep -oE 'rubric_version.*v[0-9]+' "$SKILL_ROOT/SKILL.md" | grep -oE 'v[0-9]+' | head -1 || echo "NOT_FOUND")
if [[ "$rubric_label" != "$skill_label" ]]; then
  echo "  MISMATCH: SKILL.md=$skill_label, rubric.md=$rubric_label"
  ((errors++))
else
  echo "  OK (both $skill_label)"
fi
echo ""

# ---- Check 5: SKILL.md line count ----
echo "--- Check 5: SKILL.md line count ---"
lines=$(wc -l < "$SKILL_ROOT/SKILL.md" | tr -d ' ')
if [[ "$lines" -gt 500 ]]; then
  echo "  WARNING: $lines lines (threshold: 500)"
  ((errors++))
else
  echo "  OK ($lines lines)"
fi
echo ""

# ---- Summary ----
echo "========================================"
if [[ "$errors" -eq 0 ]]; then
  echo "All checks passed."
  exit 0
else
  echo "$errors check(s) failed."
  exit 1
fi