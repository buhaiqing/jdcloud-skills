#!/bin/bash
# jdcloud-topo-discovery - Topology scan (read-only)
#
# Scans JD Cloud infrastructure for VPC topology, related resources,
# and outputs structured topology + inventory reports.
#
# Usage:
#   ./topo-scan.sh
#   ./topo-scan.sh --mode detailed --output-dir ./reports/
#   ./topo-scan.sh --assume-role jdcloud:ram::1234:role/TopologyReader
#   ./topo-scan.sh --tmp-dir /tmp/my-tmp
set -euo pipefail

# ---- Argument parsing ----
REPORT_MODE="brief"
REGION_ID="${JDC_REGION:-cn-north-1}"
OUTPUT_DIR="${TOPO_OUTPUT_DIR:-.}"
ASSUME_ROLE=""
FORMAT="both"
HEALTH_JSON=""

TOPO_TMP_EXTERNAL=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --assume-role) ASSUME_ROLE="$2"; shift 2 ;;
        --mode|-m) REPORT_MODE="$2"; shift 2 ;;
        --region|-r) REGION_ID="$2"; shift 2 ;;
        --output-dir|-o) OUTPUT_DIR="$2"; shift 2 ;;
        --format|-f) FORMAT="$2"; shift 2 ;;
        --health-json) HEALTH_JSON="$2"; shift 2 ;;
        --tmp-dir) TMP_DATA_DIR="$2"; TOPO_TMP_EXTERNAL=1; shift 2 ;;
        brief|detailed) REPORT_MODE="$1"; shift ;;
        *) echo "[ERROR] Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ---- Concurrent safety: unique temp dir per run ----
TMP_DATA_DIR="${TMP_DATA_DIR:-/tmp/topo_scan_$$_$(date +%s)}"
mkdir -p "$TMP_DATA_DIR"
export TOPO_TMP_DIR="$TMP_DATA_DIR"

# ---- STS AssumeRole (optional) ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "$ASSUME_ROLE" ]]; then
    echo "[DIAG] Using cross-account role: $ASSUME_ROLE"
    source "$SCRIPT_DIR/sts-helper.sh" --role-arn "$ASSUME_ROLE"
fi

SCAN_TIMESTAMP=$(date +%FT%T%z)

echo "[DIAG] Starting JD Cloud topology scan... Mode: $REPORT_MODE | Region: $REGION_ID | Tmp: $TMP_DATA_DIR"

# ============================================================
# Safety Gate: Read-Only Verification
# ============================================================
# Reject any command matching: create|delete|modify|update|associate|
#   disassociate|attach|detach|enable|disable|reset|start|stop|reboot|
#   restore|failover|schedule|grant|revoke|terminate|add|remove
FORBIDDEN="create|delete|modify|update|associate|disassociate|attach|detach|enable|disable|reset|start|stop|reboot|restore|failover|schedule|grant|revoke|terminate|add|remove"
_VERIFIED=""  # dedup list

verify_cmd() {
    local api_op="${1##* }"
    api_op="${api_op%% *}"
    case " $_VERIFIED " in
        *" $api_op "*) return 0 ;;
    esac
    [[ "$api_op" =~ ^($FORBIDDEN) ]] && { echo "❌ FORBIDDEN: Write operation detected - $api_op | HALT" >&2; exit 1; }
    _VERIFIED="$_VERIFIED $api_op"
    echo "   ✓ $api_op"
}

# ============================================================
# Phase 1: Parallel data collection
# ============================================================
# CRITICAL: jdc --output json MUST be placed BEFORE the subcommand.
# All commands below are read-only (describe-* / list-*).

verify_cmd "jdc vpc describe-vpcs"
jdc --output json vpc describe-vpcs --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/vpcs.json" &
PID_VPC=$!

verify_cmd "jdc lb describe-load-balancers"
jdc --output json lb describe-load-balancers --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/clbs.json" &

verify_cmd "jdc eip describe-elastic-ips"
jdc --output json eip describe-elastic-ips --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/eips.json" &

verify_cmd "jdc vpc describe-network-security-groups"
jdc --output json vpc describe-network-security-groups --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/sgs.json" &

verify_cmd "jdc ag describe-ags"
jdc --output json ag describe-ags --region-id $REGION_ID --page-size 50 > "$TMP_DATA_DIR/ags.json" &

# IAM / KMS are global resources (no --region-id)
verify_cmd "jdc iam describe-sub-users"
jdc --output json iam describe-sub-users --page-size 100 > "$TMP_DATA_DIR/iam_users.json" &

verify_cmd "jdc kms describe-key-list"
jdc --output json kms describe-key-list --page-size 100 > "$TMP_DATA_DIR/kms_keys.json" &

echo -e "\n📡 Waiting for core network resources..."
wait $PID_VPC

# Parse all VPCs for multi-VPC support
VPC_IDS=$(python3 -c "import json;d=json.load(open('$TMP_DATA_DIR/vpcs.json'));vpcs=d.get('result',{}).get('vpcs',[]);print(' '.join(v['vpcId'] for v in vpcs))" 2>/dev/null || echo "")
FIRST_VPC_ID=$(echo "$VPC_IDS" | awk '{print $1}')

if [ -n "$FIRST_VPC_ID" ]; then
    # Collect Subnets for the first VPC
    verify_cmd "jdc vpc describe-subnets"
    jdc --output json vpc describe-subnets --region-id $REGION_ID \
        --filters "vpcId=$FIRST_VPC_ID" --page-size 100 > "$TMP_DATA_DIR/subnets.json" &

    # Save multi-VPC context for renderer
    echo "$VPC_IDS" > "$TMP_DATA_DIR/multi_vpc_ids.txt"

    if [ "$REPORT_MODE" = "detailed" ]; then
        echo -e "\n📡 Phase 2: Detailed Resources..."
        verify_cmd "jdc vm describe-instances"
        jdc --output json vm describe-instances --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/vms.json" &

        verify_cmd "jdc rds describe-instances"
        jdc --output json rds describe-instances --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/rds.json" &

        verify_cmd "jdc redis describe-cache-instances"
        jdc --output json redis describe-cache-instances --region-id $REGION_ID --page-size 100 > "$TMP_DATA_DIR/redis.json" &

        echo -e "\n⏳ Waiting for detailed resources..."
    fi
else
    # No VPC found — create empty files for safety
    echo "[]" > "$TMP_DATA_DIR/subnets.json"
    echo "" > "$TMP_DATA_DIR/multi_vpc_ids.txt"
fi

# ---- Phase 2: Report Generation ----
echo -e "\n📝 Phase 3: Generating Report..."
cd "$SCRIPT_DIR"
FORMAT_ARGS="--format $FORMAT"
HEALTH_ARGS=""
[ -n "${HEALTH_JSON:-}" ] && [ -f "$HEALTH_JSON" ] && HEALTH_ARGS="--health-json $HEALTH_JSON"

# Pass temp dir to renderer via environment variable
TOPO_TMP_DIR="$TMP_DATA_DIR" python3 ./topo-render.py \
  "$OUTPUT_DIR" "$REPORT_MODE" "$SCAN_TIMESTAMP" "$REGION_ID" \
  $FORMAT_ARGS $HEALTH_ARGS

# Cleanup: only if we created the tmp dir (no explicit --tmp-dir)
if [ -z "${TOPO_TMP_EXTERNAL:-}" ]; then
    rm -rf "$TMP_DATA_DIR" 2>/dev/null || true
fi
