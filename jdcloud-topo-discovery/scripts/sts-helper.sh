#!/bin/bash
# ============================================================
# STS AssumeRole helper for jdcloud-topo-discovery.
# Sources temporary credentials from JD Cloud STS and exports them
# as JDC_ACCESS_KEY / JDC_SECRET_KEY / JDC_SESSION_TOKEN.
#
# Usage:
#   source sts-helper.sh --role-arn jdcloud:ram::1234:role/TopologyReader
#   source sts-helper.sh --role-arn "$ROLE_ARN" --session-name "topo" --duration 3600
#
# Exit codes:
#   0  - Success (caller should source this script)
#   10 - AssumeRole failed (CLI error, network, or permissions)
#   11 - Missing credentials (JDC_ACCESS_KEY not set)
#   12 - Invalid role ARN format
# ============================================================
set -euo pipefail

# ---- Defaults ----
SESSION_NAME="topo-discovery"
DURATION_SECONDS=3600

# ---- Parse args ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --role-arn) ROLE_ARN="$2"; shift 2 ;;
        --session-name) SESSION_NAME="$2"; shift 2 ;;
        --duration) DURATION_SECONDS="$2"; shift 2 ;;
        *) echo "[ERROR] Unknown option: $1" >&2; exit 12 ;;
    esac
done

if [[ -z "${ROLE_ARN:-}" ]]; then
    # No --role-arn given, nothing to do (normal path)
    exit 0
fi

# ---- Validate ARN format (JD Cloud uses jdcloud:ram:: prefix, not acs:) ----
if ! echo "$ROLE_ARN" | grep -qP '^jdcloud:ram::[0-9]+:role/.+$'; then
    echo "[ERROR] Invalid role ARN format: $ROLE_ARN" >&2
    echo "[ERROR] Expected: jdcloud:ram::<account_id>:role/<role_name>" >&2
    exit 12
fi

# ---- Check credentials ----
# jdc CLI reads from ~/.jdc/config INI, not env vars. But we need to confirm
# the config file exists and is non-empty before assuming a role.
if [[ -z "${HOME:-}" ]]; then
    HOME=/root
fi
if [[ ! -f "$HOME/.jdc/config" ]]; then
    echo "[ERROR] ~/.jdc/config not found; STS AssumeRole requires primary credentials first." >&2
    echo "[ERROR] Run: jdc configure add --access-key <AK> --secret-key <SK>" >&2
    exit 11
fi

# ---- AssumeRole ----
# Note: jdc STS API uses --assume-role-info as a JSON string (NOT individual flags).
# This is different from aliyun cli which uses --RoleArn/--RoleSessionName flags.
echo "[DIAG] Assuming role: $ROLE_ARN" >&2
ASSUME_INFO=$(printf '{"roleArn":"%s","roleSessionName":"%s","durationSeconds":%d}' \
    "$ROLE_ARN" "$SESSION_NAME" "$DURATION_SECONDS")

STS_OUTPUT=$(jdc --output json sts assume-role --assume-role-info "$ASSUME_INFO" 2>&1) || {
    echo "[ERROR] TYPE=ASSUME_ROLE_FAILED FIX=Check role ARN, permissions, and network" >&2
    echo "[ERROR] jdc sts output: $STS_OUTPUT" >&2
    exit 10
}

# ---- Extract and export credentials ----
# jdc STS response format:
# {
#   "request_id": "...",
#   "result": {
#     "credentials": {
#       "accessKeyId": "...",
#       "secretAccessKey": "...",
#       "securityToken": "...",
#       "expiration": "..."
#     }
#   }
# }
export JDC_ACCESS_KEY=$(echo "$STS_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['credentials']['accessKeyId'])")
export JDC_SECRET_KEY=$(echo "$STS_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['credentials']['secretAccessKey'])")
export JDC_SESSION_TOKEN=$(echo "$STS_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['credentials']['securityToken'])")

# Sanity: verify we got non-empty values
if [[ -z "$JDC_ACCESS_KEY" || -z "$JDC_SECRET_KEY" ]]; then
    echo "[ERROR] TYPE=EMPTY_CREDENTIALS FIX=Check STS AssumeRole response" >&2
    exit 10
fi

# For jdc CLI mode, ALSO write the temp creds to ~/.jdc/config (since CLI doesn't read env vars).
# WARNING: This overwrites the primary creds file. In sandbox, this is OK.
# In production, the caller should use a different HOME for assume-role scenarios.
cat > "$HOME/.jdc/config" << CONFIGEOF
[default]
access_key = $JDC_ACCESS_KEY
secret_key = $JDC_SECRET_KEY
region_id = ${JDC_REGION:-cn-north-1}
endpoint = vpc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > "$HOME/.jdc/current"

EXPIRY=$(echo "$STS_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['credentials'].get('expiration', 'unknown'))")
echo "[RESULT] Credentials assumed, session: $SESSION_NAME, expires: $EXPIRY" >&2
echo "[RESULT] Temp creds written to $HOME/.jdc/config (CLI mode requires this)" >&2
