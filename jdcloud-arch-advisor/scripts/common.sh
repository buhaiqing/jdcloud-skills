#!/bin/bash
# =============================================================================
# jdcloud-arch-advisor — Shared utility functions (Bash library)
# =============================================================================
# Common functions used by assess.sh (Mode B) and recommend.sh (Mode C).
#
# This file is sourced (not executed) by both entry points.
# Source guard: skip if already loaded.
# =============================================================================
# Hard rules (from AGENTS.md "Security Rules"):
#   - NEVER print / log JDC_SECRET_KEY in plain text.
#   - Use `test -n "$VAR"` to check existence; print "<masked>" if needed.
#   - jdc CLI reads credentials from ~/.jdc/config (INI) only; env vars are
#     for the Python SDK.
#   - `--output json` MUST come BEFORE the subcommand: `jdc --output json vm list`.
#   - Python 3.10 is required (jdcloud_cli==1.2.12 imports SafeConfigParser
#     which was removed in Python 3.12).
# =============================================================================

# Source guard
if [[ -n "${__JDCLOUD_ARCH_ADVISOR_COMMON_SH_LOADED:-}" ]]; then
    return 0
fi
readonly __JDCLOUD_ARCH_ADVISOR_COMMON_SH_LOADED=1

set -euo pipefail

# ---------------------------------------------------------------------------
# Colours for output
# ---------------------------------------------------------------------------
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# ---------------------------------------------------------------------------
# Configuration / directory layout
# ---------------------------------------------------------------------------
ARCH_ADVISOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RULES_DIR="${ARCH_ADVISOR_DIR}/references/rules"
TEMPLATES_DIR="${ARCH_ADVISOR_DIR}/references/scenario-templates"
OUTPUT_DIR="${ARCH_ADVISOR_DIR}/output"

mkdir -p "${OUTPUT_DIR}"

# ---------------------------------------------------------------------------
# Logging functions — NEVER print JDC_SECRET_KEY
# ---------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_debug()   { [[ "${LOG_LEVEL:-info}" == "debug" ]] && echo -e "${CYAN}[DEBUG]${NC} $*" >&2 || true; }

# ---------------------------------------------------------------------------
# Python version guard — must be 3.10 (NOT 3.12)
# jdcloud_cli 1.2.12 imports configparser.SafeConfigParser (removed in 3.12).
# ---------------------------------------------------------------------------
check_python_version() {
    if ! command -v python3 &>/dev/null; then
        log_error "python3 not found. Install Python 3.10 first:"
        log_error "  macOS:  brew install python@3.10"
        log_error "  Linux:  apt install python3.10 python3.10-dev"
        log_error "  uv:     uv python install 3.10"
        return 1
    fi
    local py_version
    py_version=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0.0")
    local py_major py_minor
    py_major=$(echo "$py_version" | cut -d. -f1)
    py_minor=$(echo "$py_version" | cut -d. -f2)

    if [[ "$py_major" -ne 3 || "$py_minor" -ne 10 ]]; then
        log_error "Python $py_version detected. JD Cloud CLI requires Python 3.10 EXACTLY."
        log_error "jdcloud_cli==1.2.12 imports SafeConfigParser (removed in Python 3.12)."
        log_error "Switch with: uv venv --python 3.10 && source .venv/bin/activate"
        return 1
    fi
    log_success "Python $py_version OK"
    return 0
}

# ---------------------------------------------------------------------------
# jdc CLI dependency check
# ---------------------------------------------------------------------------
check_jdc_cli() {
    if ! command -v jdc &>/dev/null; then
        log_error "jdc CLI not found."
        log_error "Install: uv pip install jdcloud_cli==1.2.12 jdcloud_sdk"
        return 1
    fi
    local jdc_version
    jdc_version=$(jdc --version 2>&1 | head -1 || echo "unknown")
    log_info "jdc CLI detected: ${jdc_version}"
    return 0
}

# ---------------------------------------------------------------------------
# jq dependency check (with auto-install)
# ---------------------------------------------------------------------------
check_jq() {
    if command -v jq &>/dev/null; then
        log_debug "jq $(jq --version 2>/dev/null) OK"
        return 0
    fi
    log_warn "jq not found. Attempting auto-install..."
    if install_jq; then
        if command -v jq &>/dev/null; then
            log_success "jq installed successfully"
            return 0
        fi
    fi
    log_error "jq installation failed."
    log_error "  macOS:  brew install jq"
    log_error "  Linux:  sudo apt install jq / sudo yum install jq"
    log_error "  Binary: https://jqlang.github.io/jq/download/"
    return 1
}

# Auto-install jq — same logic as alicloud-arch-advisor for parity
install_jq() {
    local os; os=$(uname -s)
    if ! curl -s --connect-timeout 3 https://github.com &>/dev/null 2>&1; then
        log_warn "Cannot reach github.com — install jq manually."
        return 1
    fi
    case "$os" in
        Darwin)
            if command -v brew &>/dev/null; then
                if brew list jq &>/dev/null 2>&1; then return 0; fi
                local brew_log; brew_log=$(mktemp)
                brew install jq >"$brew_log" 2>&1 && { rm -f "$brew_log"; return 0; }
                log_warn "brew install jq failed. Log:"
                tail -5 "$brew_log"; rm -f "$brew_log"
                return 1
            fi
            log_warn "No package manager on macOS. Install Homebrew + jq."
            return 1
            ;;
        Linux)
            local sudo_prefix=""
            [[ "$(id -u)" != "0" ]] && sudo_prefix="sudo"
            if command -v apt-get &>/dev/null; then
                DEBIAN_FRONTEND=noninteractive $sudo_prefix apt-get install -y -q jq >/dev/null 2>&1 && return 0
            elif command -v yum &>/dev/null; then
                $sudo_prefix yum install -y -q jq >/dev/null 2>&1 && return 0
            elif command -v dnf &>/dev/null; then
                $sudo_prefix dnf install -y -q jq >/dev/null 2>&1 && return 0
            fi
            # Fallback: binary download
            local arch_url=""
            case "$(uname -m)" in
                x86_64|amd64)  arch_url="https://github.com/jqlang/jq/releases/latest/download/jq-linux-amd64" ;;
                aarch64|arm64) arch_url="https://github.com/jqlang/jq/releases/latest/download/jq-linux-arm64" ;;
                *) log_warn "Unsupported arch: $(uname -m)"; return 1 ;;
            esac
            if curl -fsSL "$arch_url" -o /usr/local/bin/jq 2>/dev/null; then
                chmod +x /usr/local/bin/jq
                return 0
            fi
            return 1
            ;;
        *)
            log_warn "Unsupported OS: $os"
            return 1
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Credential checks — NEVER print the secret in plain text
# ---------------------------------------------------------------------------
# Rule: jdc CLI reads from ~/.jdc/config INI file. Environment variables
# alone are NOT picked up by the CLI (only by the Python SDK).
check_jdc_credentials() {
    local home_dir="${HOME:-/root}"
    local config_file="${home_dir}/.jdc/config"
    local current_file="${home_dir}/.jdc/current"

    if [[ ! -f "$config_file" ]]; then
        log_error "jdc CLI config not found: ${config_file}"
        log_error "Create it (INI format) — see AGENTS.md 'Credentials' section:"
        log_error "  [default]"
        log_error "  access_key = <YOUR_ACCESS_KEY>"
        log_error "  secret_key = <YOUR_SECRET_KEY>"
        log_error "  region_id  = cn-north-1"
        log_error "  endpoint   = vm.jdcloud-api.com"
        return 1
    fi
    log_info "jdc config file present: ${config_file}"

    # Read profile name from ~/.jdc/current (no trailing newline)
    local profile="default"
    if [[ -f "$current_file" ]]; then
        profile=$(cat "$current_file" 2>/dev/null | tr -d '\n\r ' || echo "default")
    fi
    log_info "jdc active profile: ${profile}"

    # Existence check (NEVER print values)
    if grep -q "^access_key" "$config_file" 2>/dev/null; then
        log_info "JDC_ACCESS_KEY present in config: <masked>"
    else
        log_warn "JDC_ACCESS_KEY not found in ${config_file}"
    fi
    if grep -q "^secret_key" "$config_file" 2>/dev/null; then
        log_info "JDC_SECRET_KEY present in config: <masked>"
    else
        log_warn "JDC_SECRET_KEY not found in ${config_file}"
    fi

    # SDK env-var check (only used by Python SDK, not jdc CLI)
    if [[ -n "${JDC_ACCESS_KEY:-}" ]]; then
        log_info "JDC_ACCESS_KEY env var present: <masked> (SDK only)"
    fi
    if [[ -n "${JDC_SECRET_KEY:-}" ]]; then
        log_info "JDC_SECRET_KEY env var present: <masked> (SDK only)"
    fi

    return 0
}

# Load credentials into the current shell (used by Python SDK only).
# NOTE: jdc CLI does NOT read environment variables — it reads ~/.jdc/config.
load_jdc_env() {
    local home_dir="${HOME:-/root}"
    local config_file="${home_dir}/.jdc/config"
    local current_file="${home_dir}/.jdc/current"

    local profile="default"
    if [[ -f "$current_file" ]]; then
        profile=$(cat "$current_file" 2>/dev/null | tr -d '\n\r ' || echo "default")
    fi

    if [[ -f "$config_file" ]]; then
        # Parse INI file with awk — never echo values
        local ak sk region
        ak=$(awk -F' *= *' -v section="[${profile}]" '
            $0 == section { in_section = 1; next }
            /^\[/ { in_section = 0 }
            in_section && $1 == "access_key" { print $2; exit }
        ' "$config_file" 2>/dev/null || true)
        sk=$(awk -F' *= *' -v section="[${profile}]" '
            $0 == section { in_section = 1; next }
            /^\[/ { in_section = 0 }
            in_section && $1 == "secret_key" { print $2; exit }
        ' "$config_file" 2>/dev/null || true)
        region=$(awk -F' *= *' -v section="[${profile}]" '
            $0 == section { in_section = 1; next }
            /^\[/ { in_section = 0 }
            in_section && $1 == "region_id" { print $2; exit }
        ' "$config_file" 2>/dev/null || true)

        # Export only if non-empty (so external overrides still win)
        [[ -n "$ak" ]] && export JDC_ACCESS_KEY="$ak"
        [[ -n "$sk" ]] && export JDC_SECRET_KEY="$sk"
        [[ -n "$region" ]] && export JDC_REGION_ID="$region"
        log_debug "Loaded jdc profile '${profile}' into env (values masked)"
    fi
}

# ---------------------------------------------------------------------------
# Top-level dependency check
# ---------------------------------------------------------------------------
check_dependencies() {
    local failed=0
    check_jdc_cli       || failed=1
    check_python_version || failed=1
    check_jq            || failed=1
    check_jdc_credentials || failed=1
    if [[ $failed -eq 1 ]]; then
        log_error "One or more dependency checks failed."
        return 1
    fi
    log_success "All dependency checks passed."
    return 0
}

# ---------------------------------------------------------------------------
# JSON path helpers (jdcloud format: $.result.<resource> in lower-case)
# ---------------------------------------------------------------------------
# Examples:
#   $.result.vpcs[0].vpcId
#   $.result.subnets[0].subnetId
#   $.result.instances[0].instanceId
# JD Cloud uses lower-case keys (vpcId / subnetId / instanceId /
# cacheInstanceId / loadBalancerId / elasticIpId) — different from
# Aliyun's PascalCase (VpcId, VSwitchId, InstanceId).

# Extract a JSON path. Usage: jdc_json_path "$json" "$.result.vpcs[0].vpcId"
jdc_json_path() {
    local json="$1"
    local path="$2"
    # Convert "$.foo.bar[0]" -> ".foo.bar[0]" for jq
    local jq_path="${path#\$.}"
    echo "$json" | jq -r "${jq_path} // empty" 2>/dev/null
}

# Get list of resource IDs (lower-case plural) from a jdc response
# Usage: jdc_resource_ids "$json" "vpcs"
jdc_resource_ids() {
    local json="$1"
    local resource_plural="$2"
    echo "$json" | jq -r ".result.${resource_plural}[]?.${resource_plural%?}Id // empty" 2>/dev/null
}

# Get total count of a resource type
# Usage: jdc_resource_count "$json" "vpcs"
jdc_resource_count() {
    local json="$1"
    local resource_plural="$2"
    echo "$json" | jq -r ".result.${resource_plural} | length // 0" 2>/dev/null
}

# Validate that a jdc CLI response looks well-formed
# Usage: jdc_validate_response "$json" "vm describe-instances"
jdc_validate_response() {
    local json="$1"
    local context="${2:-jdc call}"
    if [[ -z "$json" ]]; then
        log_error "[${context}] Empty response"
        return 1
    fi
    if ! echo "$json" | jq -e . &>/dev/null; then
        log_error "[${context}] Response is not valid JSON"
        return 1
    fi
    return 0
}

# ---------------------------------------------------------------------------
# jdc CLI wrapper with jdc-first + SDK-fallback policy
# ---------------------------------------------------------------------------
# Usage: jdc_call "vm" "describe-instances" "--instance-id" "i-xxx"
# Returns: JSON on stdout, exit code 0 on success.
# Retry policy: 0s → 2s → 4s (3 attempts) then surrender to SDK fallback.
jdc_call() {
    local product="$1"
    shift
    local max_attempts=3
    local attempt=1
    local backoff=0

    while [[ $attempt -le $max_attempts ]]; do
        if [[ $attempt -gt 1 ]]; then
            log_warn "jdc retry ${attempt}/${max_attempts} (sleep ${backoff}s) — ${product} $*"
            sleep "$backoff"
        fi
        local resp
        if resp=$(jdc --output json "$product" "$@" 2>/tmp/jdc_err.$$); then
            rm -f /tmp/jdc_err.$$
            if jdc_validate_response "$resp" "${product} $*"; then
                echo "$resp"
                return 0
            fi
        else
            log_warn "jdc call failed (attempt ${attempt}): $(cat /tmp/jdc_err.$$ 2>/dev/null | head -1)"
            rm -f /tmp/jdc_err.$$
        fi
        attempt=$((attempt + 1))
        backoff=$((backoff == 0 ? 2 : backoff * 2))
    done
    log_error "jdc call exhausted retries: ${product} $*"
    return 1
}

# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
on_error() {
    local exit_code=$?
    local line_no=${1:-unknown}
    log_error "Script failed at line ${line_no} with exit code ${exit_code}"
    exit "$exit_code"
}
trap 'on_error ${LINENO}' ERR

# ---------------------------------------------------------------------------
# WAF pillar validation
# ---------------------------------------------------------------------------
# Returns 0 if pillar is valid, 1 otherwise.
validate_pillar() {
    local pillar="$1"
    case "$pillar" in
        security|reliability|performance|cost|efficiency|all) return 0 ;;
        *) return 1 ;;
    esac
}

# Parse a comma-separated pillar list into a bash array.
# Usage: parse_pillars "security,reliability" ARRAY_NAME
parse_pillars() {
    local pillars_csv="$1"
    local __array_name="$2"
    [[ "$pillars_csv" == "all" ]] && pillars_csv="security,reliability,performance,cost,efficiency"
    IFS=',' read -ra "$__array_name" <<< "$pillars_csv"
}

# ---------------------------------------------------------------------------
# Scenario validation
# ---------------------------------------------------------------------------
validate_scenario() {
    local scenario="$1"
    case "$scenario" in
        ecommerce|gaming|fintech|saas|saas-multi-tenant|ai-ml|data-platform|microservice) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------------------------------------------------------------------------
# WAF rules loader (yaml -> index.json)
# ---------------------------------------------------------------------------
# Usage: load_rules "security,reliability" /tmp/rules.json
load_rules() {
    local pillars="$1"
    local of="${2:-${OUTPUT_DIR}/rules-index.json}"
    [[ "$pillars" == "all" ]] && pillars="security,reliability,performance,cost,efficiency"
    log_info "Loading WAF rules for pillars: ${pillars}"
    IFS=',' read -ra PL <<< "$pillars"
    local combined='{"rules":[]}'
    for p in "${PL[@]}"; do
        p=$(echo "$p" | xargs)
        local pf="${RULES_DIR}/waf-${p}.yaml"
        if [[ -f "$pf" ]]; then
            if command -v yq &>/dev/null; then
                local pr
                pr=$(yq eval -o=json '.rules[] | {id, title, description, severity, category: "'"${p}"'"}' "$pf" 2>/dev/null || echo "")
                if [[ -n "$pr" ]]; then
                    combined=$(echo "$combined" | jq --argjson new "$pr" '.rules += [$new]' 2>/dev/null || echo "$combined")
                fi
            else
                log_warn "yq not available; rules for pillar '${p}' will not be indexed"
            fi
        else
            log_warn "WAF rules file not found: ${pf} (skipping)"
        fi
    done
    echo "$combined" > "$of"
    log_success "Rules indexed → ${of}"
    cat "$of"
}

# ---------------------------------------------------------------------------
# Per-pillar scoring
# ---------------------------------------------------------------------------
# Args: pillar_name, results_json_file
# Output: JSON { "pass": N, "total": M, "score": S } where S is 0–100
pillar_score() {
    local pillar="$1"
    local results_file="${2:-${OUTPUT_DIR}/assessment-results.json}"
    [[ ! -f "$results_file" ]] && { echo '{"pass":0,"total":0,"score":0}'; return; }
    jq --arg p "$pillar" '
        .pillars[$p] as $q
        | if $q then
            {
              "pass":  ($q.results | map(select(.status == "pass"))  | length),
              "fail":  ($q.results | map(select(.status == "fail"))  | length),
              "warn":  ($q.results | map(select(.status == "warn"))  | length),
              "total": ($q.results | length),
              "score": (if ($q.results | length) > 0
                          then (($q.results | map(select(.status == "pass")) | length) * 100.0
                                / ($q.results | length))
                          else 0 end)
            }
          else
            {"pass":0,"fail":0,"warn":0,"total":0,"score":0}
          end' "$results_file"
}

# ---------------------------------------------------------------------------
# Score → grade
# ---------------------------------------------------------------------------
score_to_grade() {
    local score="${1%.*}"   # truncate float
    if [[ "$score" -ge 90 ]]; then echo "Excellent"
    elif [[ "$score" -ge 80 ]]; then echo "Good"
    elif [[ "$score" -ge 60 ]]; then echo "Warning"
    else echo "Critical"
    fi
}

# ---------------------------------------------------------------------------
# Init report skeleton (used by both assess.sh and recommend.sh)
# ---------------------------------------------------------------------------
init_report() {
    local mode="${1:-assessment}"
    local format="${2:-markdown}"
    local timestamp; timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    cat <<EOF
{
  "skill": "jdcloud-arch-advisor",
  "version": "1.0.0",
  "mode": "${mode}",
  "format": "${format}",
  "timestamp": "${timestamp}",
  "region": "${JDC_REGION_ID:-${ALICLOUD_REGION:-cn-north-1}}",
  "account": "${JDC_ACCOUNT_ID:-unknown}",
  "architecture": {},
  "pillars": {},
  "recommendations": []
}
EOF
}

# ---------------------------------------------------------------------------
# Tracer / GCL helpers (optional)
# ---------------------------------------------------------------------------
# Usage:
#   trace_path=$(init_gcl_trace "jdcloud-arch-advisor" "v1")
#   append_gcl_iteration "$trace_path" "$iter_json"
init_gcl_trace() {
    local skill="${1:-jdcloud-arch-advisor}"
    local rubric_version="${2:-v1}"
    local ts; ts=$(date -u +%Y%m%dT%H%M%SZ)
    local trace_dir="${ARCH_ADVISOR_DIR}/../audit-results"
    mkdir -p "$trace_dir"
    local trace_file="${trace_dir}/gcl-trace-${ts}.json"
    cat > "$trace_file" <<EOF
{
  "skill": "${skill}",
  "rubric_version": "${rubric_version}",
  "iterations": [],
  "final": null
}
EOF
    echo "$trace_file"
}

append_gcl_iteration() {
    local trace_path="$1"
    local iter_json="$2"
    local tmp; tmp=$(mktemp)
    jq --argjson iter "$iter_json" '.iterations += [$iter]' "$trace_path" > "$tmp" \
        && mv "$tmp" "$trace_path" \
        || { rm -f "$tmp"; log_warn "Failed to append GCL iteration"; return 1; }
}

# ---------------------------------------------------------------------------
# Cleanup on exit
# ---------------------------------------------------------------------------
cleanup_tmp_files() {
    rm -f /tmp/jdc_err.$$ 2>/dev/null || true
    # Preserve any .tmp files in OUTPUT_DIR created by callers (no-op by default)
}
trap cleanup_tmp_files EXIT

# ---------------------------------------------------------------------------
# Mark module loaded
# ---------------------------------------------------------------------------
log_debug "common.sh loaded (JD Cloud arch-advisor v1.0.0)"
