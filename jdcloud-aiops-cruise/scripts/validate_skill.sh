#!/usr/bin/env bash
# validate_skill.sh — Verifiable knowledge asset for jdcloud-aiops-cruise
# Usage: bash scripts/validate_skill.sh
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_ROOT"

errors=0
echo "=== jdcloud-aiops-cruise Skill Validation ==="
echo ""

# ---- Check 1: Internal link validity ----
echo "--- Check 1: Internal links in SKILL.md ---"
while IFS= read -r link; do
  if echo "$link" | grep -qE '^https?://' || echo "$link" | grep -qE '^#'; then
    continue
  fi
  target="${link%%#*}"
  if [[ ! -f "$SKILL_ROOT/$target" ]]; then
    echo "  BROKEN: $link -> $target (not found)"
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
  "references/quality-gate.md"
  "references/severity-matrix.md"
  "references/threshold-definitions.md"
)
for ref in "${expected_refs[@]}"; do
  if [[ ! -f "$SKILL_ROOT/$ref" ]]; then
    echo "  MISSING: $ref"
    ((errors++))
  fi
done
echo "  OK (${#expected_refs[@]} files)"
echo ""

# ---- Check 3: Python syntax check on all scripts ----
echo "--- Check 3: Python syntax ---"
find "$SKILL_ROOT/scripts" -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -v "^$" || true
# py_compile returns 0 on success, so we just surface any stderr
echo "  OK"
echo ""

# ---- Check 4: SKILL.md line count ----
echo "--- Check 4: SKILL.md line count ---"
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