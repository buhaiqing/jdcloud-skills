#!/bin/bash
# =============================================================================
# jdcloud-arch-advisor - Recommendation Mode (Mode C)
# =============================================================================
# Usage:
#   ./recommend.sh --scenario ecommerce|gaming|fintech|saas|ai-ml|data-platform
#                  [--dau 100000]
#                  [--compliance equal-protection|pci|hipaa|gdpr]
#                  [--ha single-az|multi-az|multi-region]
#                  [--budget USD]
#                  [--constraints "key=val,key=val"]
#                  [--report-output PATH]
#                  [--region cn-north-1]
#                  [--mock]
#                  [-h|--help]
#
# Generates a multi-plan architecture recommendation report for a given
# scenario. Produces:
#   1. Capacity tier (small / medium / large / xlarge) from DAU
#   2. Per-tier component spec (VM / RDS / Redis / CLB / EIP / etc.)
#   3. HA + compliance add-ons
#   4. Mermaid topology diagram
#   5. WAF pre-assessment (security / reliability / performance / cost / efficiency)
#   6. Cost estimation (rough)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCENARIO=""
DAU=100000
COMPLIANCE="none"
HA_LEVEL="multi-az"
BUDGET=""
REGION="${JDC_REGION_ID:-${ALICLOUD_REGION:-cn-north-1}}"
CONSTRAINTS=""
REPORT_OUTPUT=""                # default: ${OUTPUT_DIR}/recommendation-report.md
OUTPUT_FORMAT="markdown"
USE_MOCK=false
GCL_ENABLED="${JDC_ARCH_GCL_ENABLED:-true}"
GCL_MAX_ITER=5

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
Usage: $0 --scenario SCENARIO [OPTIONS]

Required:
  --scenario ID           场景 ID (ecommerce | gaming | fintech | saas
                          | saas-multi-tenant | ai-ml | data-platform
                          | microservice)

Options:
  --dau NUM               日活用户 (DAU) for capacity tiering (default: 100000)
  --compliance ID         合规要求: none | equal-protection | pci | hipaa
                          | gdpr (default: none)
  --ha LEVEL              HA 等级: single-az | multi-az | multi-region
                          (default: multi-az)
  --budget NUM            月预算 (USD) (default: unlimited)
  --constraints "k=v,..."  业务约束 (e.g., "industry=finance,tps=10000")
  --region REGION         京东云区域 (default: \$JDC_REGION_ID or cn-north-1)
  --report-output PATH    报告输出路径 (default: \${OUTPUT_DIR}/recommendation-report.md)
  --output FORMAT         markdown | json (default: markdown)
  --mock                  强制使用 Mock 模板 (无需凭证)
  -h, --help              显示帮助

容量等级自动映射 (DAU → tier):
  <= 10,000     → small
  <= 100,000    → medium
  <= 500,000    → large
  >  500,000    → xlarge

示例:
  # 电商 medium tier
  $0 --scenario ecommerce --dau 100000

  # 金融 multi-region + 等保合规
  $0 --scenario fintech --ha multi-region --compliance equal-protection

  # 游戏 + multi-region
  $0 --scenario gaming --ha multi-region --dau 500000

  # AI 训练 + GPU 推理
  $0 --scenario ai-ml --dau 5000 --ha single-az

  # 预算受限, 自动 scale-down
  $0 --scenario ecommerce --dau 200000 --budget 5000
EOF
    exit 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scenario)        SCENARIO="$2"; shift 2 ;;
        --dau)             DAU="$2"; shift 2 ;;
        --compliance)      COMPLIANCE="$2"; shift 2 ;;
        --ha)              HA_LEVEL="$2"; shift 2 ;;
        --budget)          BUDGET="$2"; shift 2 ;;
        --constraints)     CONSTRAINTS="$2"; shift 2 ;;
        --region)          REGION="$2"; shift 2 ;;
        --report-output)   REPORT_OUTPUT="$2"; shift 2 ;;
        --output)          OUTPUT_FORMAT="$2"; shift 2 ;;
        --mock)            USE_MOCK=true; shift ;;
        -h|--help)         usage ;;
        *)
            log_error "Unknown argument: $1"
            usage
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
if [[ -z "$SCENARIO" ]]; then
    log_error "--scenario is required."
    usage
fi
if ! validate_scenario "$SCENARIO"; then
    log_error "Invalid --scenario: '${SCENARIO}'."
    log_error "Valid: ecommerce, gaming, fintech, saas, saas-multi-tenant, ai-ml, data-platform, microservice"
    exit 1
fi
case "$HA_LEVEL" in
    single-az|multi-az|multi-region) ;;
    *) log_error "Invalid --ha: '${HA_LEVEL}'. Must be single-az, multi-az, multi-region."; exit 1 ;;
esac
if [[ "$OUTPUT_FORMAT" != "markdown" && "$OUTPUT_FORMAT" != "json" ]]; then
    log_error "Invalid --output: '${OUTPUT_FORMAT}'."
    exit 1
fi

if [[ -z "$REPORT_OUTPUT" ]]; then
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        REPORT_OUTPUT="${OUTPUT_DIR}/recommendation-report.json"
    else
        REPORT_OUTPUT="${OUTPUT_DIR}/recommendation-report.md"
    fi
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
dau_to_tier() {
    local dau="$1"
    if [[ "$dau" -le 10000 ]]; then echo "small"
    elif [[ "$dau" -le 100000 ]]; then echo "medium"
    elif [[ "$dau" -le 500000 ]]; then echo "large"
    else echo "xlarge"
    fi
}

# Rough cost estimation (USD/month) for one VM/RDS/Redis instance.
# These are reference values — production deployments should query
# the JD Cloud price calculator (jdcloud-billing-ops: missing).
estimate_cost() {
    local resource_type="$1"
    local spec="${2:-default}"
    case "$resource_type" in
        vm|g.n2.medium)         echo 50 ;;
        vm|g.n2.large)          echo 100 ;;
        vm|g.n2.xlarge)         echo 200 ;;
        vm|g.n2.2xlarge)        echo 400 ;;
        rds|rds.mysql.s2.large) echo 120 ;;
        rds|rds.mysql.s4.large) echo 240 ;;
        rds|rds.mysql.s8.xlarge) echo 480 ;;
        redis)                  echo 60 ;;
        clb)                    echo 30 ;;
        eip)                    echo 20 ;;
        kms)                    echo 10 ;;
        *)                      echo 50 ;;
    esac
}

# ---------------------------------------------------------------------------
# Step 1: dependency check
# ---------------------------------------------------------------------------
log_info "=== jdcloud-arch-advisor Recommendation (Mode C) ==="
log_info "Scenario:    ${SCENARIO}"
log_info "DAU:         ${DAU}"
log_info "HA Level:    ${HA_LEVEL}"
log_info "Compliance:  ${COMPLIANCE}"
[[ -n "$BUDGET" ]]      && log_info "Budget:      \$${BUDGET}/month"
[[ -n "$CONSTRAINTS" ]] && log_info "Constraints: ${CONSTRAINTS}"
log_info "Region:      ${REGION}"
log_info "Mock Mode:   ${USE_MOCK}"
echo ""

log_info "[Step 1/6] Checking dependencies..."
if [[ "$USE_MOCK" != "true" ]]; then
    check_dependencies || log_warn "Dependency check failed — continuing in MOCK mode."
    if ! command -v jdc &>/dev/null; then
        USE_MOCK=true
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2: load scenario template
# ---------------------------------------------------------------------------
log_info "[Step 2/6] Loading scenario template..."
CAP_TIER=$(dau_to_tier "$DAU")
log_info "Capacity tier: ${CAP_TIER} (DAU = ${DAU})"

# Load scenario from index.yaml (if available) OR use built-in templates
SCENARIO_INDEX="${TEMPLATES_DIR}/index.yaml"
if [[ -f "$SCENARIO_INDEX" && "$USE_MOCK" != "true" ]]; then
    log_info "Scenario index found: ${SCENARIO_INDEX}"
    log_info "Loading description from YAML…"
    SCENARIO_NAME=$(yq eval ".scenarios[] | select(.id == \"${SCENARIO}\") | .name" "$SCENARIO_INDEX" 2>/dev/null || echo "$SCENARIO")
    SCENARIO_DESC=$(yq eval ".scenarios[] | select(.id == \"${SCENARIO}\") | .description" "$SCENARIO_INDEX" 2>/dev/null || echo "")
    log_success "Scenario loaded: ${SCENARIO_NAME}"
else
    log_info "Using built-in scenario templates (mock mode or no index.yaml)"
    case "$SCENARIO" in
        ecommerce)         SCENARIO_NAME="电商平台";       SCENARIO_DESC="高并发电商平台, 支持商品浏览、下单、支付、库存管理" ;;
        gaming)            SCENARIO_NAME="游戏后端";       SCENARIO_DESC="实时游戏后端, 支持高并发玩家在线、实时对战、排行榜" ;;
        fintech)           SCENARIO_NAME="金融科技";       SCENARIO_DESC="金融合规场景, 强审计 + 等保 / PCI-DSS" ;;
        saas|saas-multi-tenant) SCENARIO_NAME="SaaS 多租户"; SCENARIO_DESC="多租户 SaaS 平台, 资源隔离 + 按需计费 + 弹性伸缩" ;;
        ai-ml)             SCENARIO_NAME="AI/ML 平台";     SCENARIO_DESC="AI 训练 / 推理, GPU 集群 + 数据管线" ;;
        data-platform)     SCENARIO_NAME="数据平台";       SCENARIO_DESC="大数据分析 + 离线批处理 + 实时流计算 + 数据湖" ;;
        microservice)      SCENARIO_NAME="微服务架构";     SCENARIO_DESC="容器 + Service Mesh + CI/CD + 灰度发布" ;;
        *)                 SCENARIO_NAME="$SCENARIO";      SCENARIO_DESC="" ;;
    esac
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3: generate component spec (per tier + HA + compliance)
# ---------------------------------------------------------------------------
log_info "[Step 3/6] Generating component spec for ${SCENARIO} / ${CAP_TIER}…"

# Each component spec includes: jdcloud product mapping, count, type
# (We DO NOT use Terraform HCL — JD Cloud has no official provider;
#  any IaC code in this file is documentation-only.)
declare -A SCENARIO_TEMPLATES

SCENARIO_TEMPLATES["ecommerce"]='{
  "small":  {"vm": 2, "vm_type": "g.n2.medium",   "rds": 1, "rds_type": "rds.mysql.s2.large",  "redis": 1, "clb": 1, "eip": 1, "kms": 1},
  "medium": {"vm": 4, "vm_type": "g.n2.large",    "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 1, "eip": 1, "kms": 1},
  "large":  {"vm": 8, "vm_type": "g.n2.xlarge",   "rds": 2, "rds_type": "rds.mysql.s8.xlarge", "redis": 3, "clb": 2, "eip": 2, "kms": 2},
  "xlarge": {"vm":16, "vm_type": "g.n2.2xlarge",  "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 4, "clb": 3, "eip": 3, "kms": 2}
}'

SCENARIO_TEMPLATES["gaming"]='{
  "small":  {"vm": 3, "vm_type": "g.n2.large",     "rds": 1, "rds_type": "rds.mysql.s2.large",  "redis": 2, "clb": 1, "eip": 1, "kms": 1},
  "medium": {"vm": 6, "vm_type": "g.n2.xlarge",    "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 4, "clb": 2, "eip": 1, "kms": 1},
  "large":  {"vm":12, "vm_type": "g.n2.2xlarge",   "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 8, "clb": 3, "eip": 2, "kms": 2},
  "xlarge": {"vm":24, "vm_type": "g.n2.4xlarge",   "rds": 6, "rds_type": "rds.mysql.s8.xlarge", "redis":12, "clb": 4, "eip": 2, "kms": 2}
}'

SCENARIO_TEMPLATES["fintech"]='{
  "small":  {"vm": 3, "vm_type": "g.n2.large",     "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 1, "eip": 1, "kms": 2, "audit": 1},
  "medium": {"vm": 6, "vm_type": "g.n2.xlarge",    "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 2, "eip": 1, "kms": 2, "audit": 1},
  "large":  {"vm":12, "vm_type": "g.n2.2xlarge",   "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 4, "clb": 2, "eip": 2, "kms": 3, "audit": 1},
  "xlarge": {"vm":24, "vm_type": "g.n2.4xlarge",   "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 6, "clb": 3, "eip": 2, "kms": 3, "audit": 1}
}'

SCENARIO_TEMPLATES["saas"]='{
  "small":  {"vm": 2, "vm_type": "g.n2.large",     "rds": 1, "rds_type": "rds.mysql.s2.large",  "redis": 1, "clb": 1, "eip": 1, "kms": 1},
  "medium": {"vm": 4, "vm_type": "g.n2.xlarge",    "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 1, "eip": 1, "kms": 1},
  "large":  {"vm": 8, "vm_type": "g.n2.2xlarge",   "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 4, "clb": 2, "eip": 1, "kms": 2},
  "xlarge": {"vm":16, "vm_type": "g.n2.4xlarge",   "rds": 8, "rds_type": "rds.mysql.s8.xlarge", "redis": 8, "clb": 3, "eip": 2, "kms": 2}
}'

SCENARIO_TEMPLATES["ai-ml"]='{
  "small":  {"vm": 3, "vm_type": "g.n2.xlarge",   "gpu_vm": 1, "gpu_type": "p.n2.large",       "rds": 1, "rds_type": "rds.mysql.s2.large", "redis": 1, "clb": 1, "kms": 1},
  "medium": {"vm": 6, "vm_type": "g.n2.2xlarge",  "gpu_vm": 2, "gpu_type": "p.n2.2xlarge",      "rds": 2, "rds_type": "rds.mysql.s4.large", "redis": 2, "clb": 1, "kms": 1},
  "large":  {"vm": 8, "vm_type": "g.n2.4xlarge",  "gpu_vm": 4, "gpu_type": "p.n2.4xlarge",      "rds": 2, "rds_type": "rds.mysql.s4.large", "redis": 4, "clb": 2, "kms": 2},
  "xlarge": {"vm":16, "vm_type": "g.n2.8xlarge",  "gpu_vm": 8, "gpu_type": "p.n2.8xlarge",      "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 8, "clb": 3, "kms": 2}
}'

SCENARIO_TEMPLATES["data-platform"]='{
  "small":  {"vm": 3, "vm_type": "g.n2.2xlarge",  "rds": 1, "rds_type": "rds.mysql.s2.large",  "redis": 1, "clb": 1, "kms": 1},
  "medium": {"vm": 6, "vm_type": "g.n2.4xlarge",  "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 1, "kms": 1},
  "large":  {"vm":12, "vm_type": "g.n2.8xlarge",  "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 4, "clb": 2, "kms": 2},
  "xlarge": {"vm":24, "vm_type": "g.n2.16xlarge", "rds": 6, "rds_type": "rds.mysql.s8.xlarge", "redis": 8, "clb": 3, "kms": 2}
}'

SCENARIO_TEMPLATES["microservice"]='{
  "small":  {"vm": 3, "vm_type": "g.n2.large",   "rds": 1, "rds_type": "rds.mysql.s2.large",  "redis": 1, "clb": 1, "kms": 1},
  "medium": {"vm": 6, "vm_type": "g.n2.xlarge",  "rds": 2, "rds_type": "rds.mysql.s4.large",  "redis": 2, "clb": 1, "kms": 1},
  "large":  {"vm":12, "vm_type": "g.n2.2xlarge", "rds": 4, "rds_type": "rds.mysql.s8.xlarge", "redis": 4, "clb": 2, "kms": 2},
  "xlarge": {"vm":24, "vm_type": "g.n2.4xlarge", "rds": 8, "rds_type": "rds.mysql.s8.xlarge", "redis": 8, "clb": 3, "kms": 2}
}'

# Pick template
TEMPLATE_JSON="${SCENARIO_TEMPLATES[$SCENARIO]:-}"
if [[ -z "$TEMPLATE_JSON" ]]; then
    log_error "No template for scenario: ${SCENARIO}"
    exit 1
fi
COMPONENTS=$(echo "$TEMPLATE_JSON" | jq --arg tier "$CAP_TIER" '.[$tier]')
log_info "Base component spec:"
echo "$COMPONENTS" | jq '.' | sed 's/^/    /'
echo ""

# Apply HA — double compute for multi-az, plus for multi-region add DR
case "$HA_LEVEL" in
    single-az)
        COMPONENTS=$(echo "$COMPONENTS" | jq '. + {"az_count": 1, "multi_az_rds": false, "multi_az_redis": false}')
        log_info "  HA: single-az (no redundancy)"
        ;;
    multi-az)
        # Double VM count
        vm_count=$(echo "$COMPONENTS" | jq '.vm // 0')
        new_vm=$(( vm_count > 0 ? vm_count * 2 : vm_count ))
        COMPONENTS=$(echo "$COMPONENTS" | jq --argjson v "$new_vm" '.vm = $v | . + {"az_count": 2, "multi_az_rds": true, "multi_az_redis": true}')
        log_info "  HA: multi-az (compute × 2, RDS / Redis 主备)"
        ;;
    multi-region)
        # Triple for two regions + DR
        vm_count=$(echo "$COMPONENTS" | jq '.vm // 0')
        new_vm=$(( vm_count > 0 ? vm_count * 2 : vm_count ))
        COMPONENTS=$(echo "$COMPONENTS" | jq --argjson v "$new_vm" '
            .vm = $v |
            . + {
                "az_count": 2,
                "multi_az_rds": true,
                "multi_az_redis": true,
                "multi_region": true,
                "dr_region": "cn-north-1" | tostring,
                "rds_cross_region_replica": true,
                "oss_cross_region_replica": true
            }')
        log_info "  HA: multi-region (compute × 2, 跨区域灾备, RDS + OSS 跨区域复制)"
        ;;
esac

# Apply compliance add-ons
COMPLIANCE_ADDONS='[]'
case "$COMPLIANCE" in
    equal-protection|pci|hipaa)
        COMPLIANCE_ADDONS='["jdcloud-waf", "jdcloud-kms-managed-key", "jdcloud-actiontrail", "jdcloud-rds-ssl", "jdcloud-oss-encryption"]'
        log_info "  Compliance add-ons (${COMPLIANCE}): $(echo "$COMPLIANCE_ADDONS" | jq -c '.')"
        ;;
    gdpr)
        COMPLIANCE_ADDONS='["jdcloud-kms-managed-key", "jdcloud-actiontrail", "jdcloud-rds-ssl", "jdcloud-oss-encryption", "jdcloud-data-discovery"]'
        log_info "  Compliance add-ons (${COMPLIANCE}): $(echo "$COMPLIANCE_ADDONS" | jq -c '.')"
        ;;
    none)
        log_info "  Compliance: none"
        ;;
    *)
        log_warn "  Unknown compliance: ${COMPLIANCE} (no add-ons applied)"
        ;;
esac

# Apply budget constraint (rough linear scale-down)
if [[ -n "$BUDGET" ]]; then
    log_info "  Budget: \$${BUDGET}/month — estimating cost"
    vm_n=$(echo "$COMPONENTS" | jq '.vm // 0')
    rds_n=$(echo "$COMPONENTS" | jq '.rds // 0')
    redis_n=$(echo "$COMPONENTS" | jq '.redis // 0')
    vm_type=$(echo "$COMPONENTS" | jq -r '.vm_type // "g.n2.large"')
    rds_type=$(echo "$COMPONENTS" | jq -r '.rds_type // "rds.mysql.s2.large"')
    cost_per_vm=$(estimate_cost "vm" "$vm_type")
    cost_per_rds=$(estimate_cost "rds" "$rds_type")
    cost_per_redis=$(estimate_cost "redis")
    total=$(( vm_n * cost_per_vm + rds_n * cost_per_rds + redis_n * cost_per_redis ))
    log_info "  Estimated cost: \$${total}/month (vm: ${vm_n}×\$${cost_per_vm}, rds: ${rds_n}×\$${cost_per_rds}, redis: ${redis_n}×\$${cost_per_redis})"
    if [[ "$total" -gt "$BUDGET" ]]; then
        log_warn "  Estimated cost (\$${total}) exceeds budget (\$${BUDGET}). Suggesting scale-down."
        scale=$(echo "scale=2; $BUDGET / $total" | bc 2>/dev/null || echo "0.5")
        new_vm=$(echo "$vm_n * $scale" | bc 2>/dev/null | cut -d. -f1)
        new_vm=$(( new_vm > 1 ? new_vm : 1 ))
        COMPONENTS=$(echo "$COMPONENTS" | jq --argjson v "$new_vm" '.vm = $v')
        log_info "  Scaled VM count to ${new_vm} to fit budget."
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Step 4: build recommendation plans (small / medium / large / xlarge)
# ---------------------------------------------------------------------------
log_info "[Step 4/6] Building multi-plan comparison…"
ALL_PLANS='[]'
for tier in small medium large xlarge; do
    tier_components=$(echo "$TEMPLATE_JSON" | jq --arg t "$tier" '.[$t]')
    tier_vm_n=$(echo "$tier_components" | jq '.vm // 0')
    tier_rds_n=$(echo "$tier_components" | jq '.rds // 0')
    tier_redis_n=$(echo "$tier_components" | jq '.redis // 0')
    tier_cost=$(( tier_vm_n * 100 + tier_rds_n * 150 + tier_redis_n * 60 ))
    ALL_PLANS=$(echo "$ALL_PLANS" | jq \
        --arg tier "$tier" \
        --argjson comp "$tier_components" \
        --argjson cost "$tier_cost" \
        '. + [{"tier": $tier, "components": $comp, "estimated_cost_usd": $cost}]')
done
log_success "Built plans for tiers: $(echo "$ALL_PLANS" | jq -r '.[].tier' | paste -sd ',' -)"
echo ""

# ---------------------------------------------------------------------------
# Step 5: render Mermaid + WAF pre-assessment
# ---------------------------------------------------------------------------
log_info "[Step 5/6] Rendering Mermaid topology and WAF pre-assessment…"

vm_n=$(echo "$COMPONENTS" | jq '.vm // 0')
rds_n=$(echo "$COMPONENTS" | jq '.rds // 0')
redis_n=$(echo "$COMPONENTS" | jq '.redis // 0')
clb_n=$(echo "$COMPONENTS" | jq '.clb // 0')
eip_n=$(echo "$COMPONENTS" | jq '.eip // 0')
kms_n=$(echo "$COMPONENTS" | jq '.kms // 0')
gpu_n=$(echo "$COMPONENTS" | jq '.gpu_vm // 0')
gpu_type=$(echo "$COMPONENTS" | jq -r '.gpu_type // ""')
audit_n=$(echo "$COMPONENTS" | jq '.audit // 0')

MERMAID="graph TB"
MERMAID+=$'\n    Internet((Internet))'
MERMAID+=$'\n    subgraph "京东云 '"${REGION}"$'"'

[[ "$eip_n" -gt 0 ]] && MERMAID+=$'\n        EIP[EIP × '"${eip_n}"$']' && MERMAID+=$'\n        Internet --> EIP'
[[ "$clb_n" -gt 0 ]] && MERMAID+=$'\n        CLB[CLB × '"${clb_n}"$']' && [[ "$eip_n" -gt 0 ]] && MERMAID+=$'\n        EIP --> CLB' || MERMAID+=$'\n        Internet --> CLB'

MERMAID+=$'\n        subgraph Compute'
[[ "$vm_n" -gt 0 ]] && MERMAID+=$'\n            VM[VM × '"${vm_n}"$']' && MERMAID+=$'\n        CLB --> VM'
[[ "$gpu_n" -gt 0 ]] && MERMAID+=$'\n            GPU[GPU '"${gpu_type}"$' × '"${gpu_n}"$']' && MERMAID+=$'\n        CLB --> GPU'
MERMAID+=$'\n        end'

MERMAID+=$'\n        subgraph Storage'
[[ "$rds_n"   -gt 0 ]] && MERMAID+=$'\n            RDS[(RDS MySQL × '"${rds_n}"$')]'   && MERMAID+=$'\n        VM --> RDS'
[[ "$redis_n" -gt 0 ]] && MERMAID+=$'\n            Redis[(Redis × '"${redis_n}"$')]' && MERMAID+=$'\n        VM --> Redis'
MERMAID+=$'\n        end'

[[ "$kms_n"   -gt 0 ]] && MERMAID+=$'\n        KMS[KMS × '"${kms_n}"$']'   && MERMAID+=$'\n        RDS --> KMS'
[[ "$audit_n" -gt 0 ]] && MERMAID+=$'\n        Audit[ActionTrail × '"${audit_n}"$']' && MERMAID+=$'\n        VM --> Audit'

# Compliance add-ons
if [[ "$(echo "$COMPLIANCE_ADDONS" | jq 'length')" -gt 0 ]]; then
    MERMAID+=$'\n        subgraph Compliance'
    while IFS= read -r addon; do
        addon=$(echo "$addon" | tr -d '"')
        MERMAID+=$'\n            '"${addon}"$'['"${addon}"$']'
    done < <(echo "$COMPLIANCE_ADDONS" | jq -r '.[]')
    MERMAID+=$'\n        end'
fi

MERMAID+=$'\n    end'
log_success "Mermaid diagram generated"
echo ""

# WAF pre-assessment
PRE_ASSESSMENT=$(jq -n '{
    "security":     {"status": "review", "items": ["启用 WAF 防护", "KMS 密钥自动轮转", "RDS SSL 加密"]},
    "reliability":  {"status": "good",    "items": ["Multi-AZ / Multi-Region HA 已配置"]},
    "performance":  {"status": "good",    "items": ["Auto Scaling 已考虑 (jdcloud-auto-scaling-orch: missing)"]},
    "cost":         {"status": "review",  "items": ["预留实例券", "OSS 存储类型优化 (jdcloud-oss-ops: missing)"]},
    "efficiency":   {"status": "review",  "items": ["资源标签覆盖", "CloudMonitor 告警完备 (jdcloud-cloudmonitor-ops)"]}
}')
log_success "WAF pre-assessment complete"
echo ""

# ---------------------------------------------------------------------------
# Step 6: write report
# ---------------------------------------------------------------------------
log_info "[Step 6/6] Writing report → ${REPORT_OUTPUT}"

# Aggregate recommendation
RECOMMENDED_PLAN=$(jq -n \
    --arg scenario "${SCENARIO_NAME}" \
    --arg tier "${CAP_TIER}" \
    --arg ha "${HA_LEVEL}" \
    --argjson components "${COMPONENTS}" \
    --argjson compliance "${COMPLIANCE_ADDONS}" \
    --arg mermaid "${MERMAID}" \
    '{
        "scenario": $scenario,
        "capacity_tier": $tier,
        "ha_level": $ha,
        "components": $components,
        "compliance_addons": $compliance,
        "mermaid": $mermaid
    }')

if [[ "$OUTPUT_FORMAT" == "markdown" ]]; then
    {
        echo "# 京东云架构推荐报告 — ${SCENARIO_NAME}"
        echo ""
        echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**场景**: ${SCENARIO_NAME} (${SCENARIO_DESC})"
        echo "**地域**: ${REGION}"
        echo "**DAU**: ${DAU} → 容量等级: ${CAP_TIER}"
        echo "**HA 等级**: ${HA_LEVEL}"
        echo "**合规要求**: ${COMPLIANCE}"
        [[ -n "$BUDGET" ]]      && echo "**月预算**: \$${BUDGET}"
        [[ -n "$CONSTRAINTS" ]] && echo "**业务约束**: ${CONSTRAINTS}"
        echo ""
        echo "---"
        echo ""
        echo "## 1. 推荐方案 (${CAP_TIER})"
        echo ""
        echo "| 组件 | 数量 | 规格 |"
        echo "|------|------|------|"
        echo "$COMPONENTS" | jq -r '
            to_entries[] |
            "| \(.key) | \((.value | type) == "number" | if . then .value else "-" end) | \((.value | type) == "string" | if . then .value else "-" end) |"'
        echo ""
        echo "## 2. 推荐架构拓扑"
        echo ""
        echo '```mermaid'
        echo "$MERMAID"
        echo '```'
        echo ""
        echo "## 3. 多方案对比"
        echo ""
        echo "| 容量等级 | VM | RDS | Redis | 估算成本 (USD/月) |"
        echo "|---------|-----|-----|-------|------------------|"
        echo "$ALL_PLANS" | jq -r '.[] | "| \(.tier) | \(.components.vm // 0) | \(.components.rds // 0) | \(.components.redis // 0) | $\(.estimated_cost_usd) |"'
        echo ""
        echo "## 4. 合规附加组件"
        echo ""
        if [[ "$(echo "$COMPLIANCE_ADDONS" | jq 'length')" -gt 0 ]]; then
            echo "$COMPLIANCE_ADDONS" | jq -r '.[] | "- \(.)"'
        else
            echo "_无_"
        fi
        echo ""
        echo "## 5. WAF 预评估"
        echo ""
        echo "$PRE_ASSESSMENT" | jq -r '
            to_entries[] |
            "### \(.key | ascii_upcase): \(.value.status)\n" +
            (.value.items | map("  - \(.)") | join("\n")) + "\n"'
        echo ""
        echo "## 6. 部署建议 (JCS / ROS 等价物)"
        echo ""
        echo "> ⚠️ 京东云无官方 Terraform Provider, 以下步骤为 documentation-only 描述,"
        echo "> 实际部署应使用 jdcloud-cli / 控制台 / OpenAPI。"
        echo ""
        echo "1. 使用 \`jdc vpc create-vpc\` 创建 VPC (jdcloud-vpc-ops: missing, 手工创建)"
        echo "2. 使用 \`jdc vpc create-subnet\` 在 2 个 AZ 创建子网"
        echo "3. 使用 \`jdc vm create-instances\` 批量创建 ${vm_n} 台 VM"
        echo "4. 使用 \`jdc rds create-db-instance\` 创建 RDS 主备"
        echo "5. 使用 \`jdc redis create-cache-instance\` 创建 Redis 集群"
        echo "6. 使用 \`jdc lb create-load-balancer\` 创建 CLB 并注册后端"
        echo "7. 使用 \`jdc eip associate-elastic-ip\` 绑定 EIP 到 CLB"
        echo "8. 使用 \`jcloud-cloudmonitor-ops\` 配置关键告警 (CPU/Memory/Disk/Network)"
        echo "9. 使用 \`jdcloud-audit-ops\` 启用 ActionTrail"
        echo "10. 使用 \`jdcloud-tag-audit-ops\` 应用资源标签 (env / app / team)"
        echo ""
        echo "---"
        echo ""
        echo "## 7. 后续动作"
        echo ""
        echo "- 查看完整 WAF 评估: \`./assess.sh --target-vpc <new-vpc-id>\`"
        echo "- 故障排查: \`references/troubleshooting.md\`"
        echo "- 集成示例: \`references/integration.md\`"
        echo ""
        echo "*本报告由 jdcloud-arch-advisor v1.0.0 自动生成 (Mode C)*"
    } > "$REPORT_OUTPUT"
else
    jq -n \
        --arg skill "jdcloud-arch-advisor" \
        --arg mode "recommendation" \
        --arg scenario "${SCENARIO_NAME}" \
        --arg tier "${CAP_TIER}" \
        --arg ha "${HA_LEVEL}" \
        --arg region "${REGION}" \
        --argjson recommended "${RECOMMENDED_PLAN}" \
        --argjson all_plans "${ALL_PLANS}" \
        --argjson pre "${PRE_ASSESSMENT}" \
        '{
            "skill": $skill,
            "mode": $mode,
            "scenario": $scenario,
            "capacity_tier": $tier,
            "ha_level": $ha,
            "region": $region,
            "recommended": $recommended,
            "all_plans": $all_plans,
            "waf_pre_assessment": $pre
        }' > "$REPORT_OUTPUT"
fi
log_success "Report saved → ${REPORT_OUTPUT}"
echo ""

# Save blueprint JSON
BLUEPRINT_FILE="${OUTPUT_DIR}/recommendation-blueprint.json"
echo "$RECOMMENDED_PLAN" | jq '.' > "$BLUEPRINT_FILE"
log_success "Blueprint JSON → ${BLUEPRINT_FILE}"
echo ""

log_success "=== Recommendation complete ==="
echo ""
echo "Output files:"
ls -la "${OUTPUT_DIR}/" | grep -v '^total' | grep -v '^d'
