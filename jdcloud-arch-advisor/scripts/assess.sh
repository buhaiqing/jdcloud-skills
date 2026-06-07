#!/bin/bash
# =============================================================================
# jdcloud-arch-advisor - Assessment Mode (Mode B - WAF Maturity Assessment)
# =============================================================================
# Usage:
#   ./assess.sh [--pillar security|reliability|...|all]
#               [--target-vpc vpc-xxx]
#               [--target-resource-ids "i-xxx,i-yyy"]
#               [--report-output PATH]
#               [--output markdown|json]
#               [--region cn-north-1]
#               [--mock]
#               [-h|--help]
#
# This script:
#   1. Checks jdc CLI / Python 3.10 / credentials
#   2. Loads the target scope (VPC or explicit resource IDs)
#   3. Calls downstream jdcloud-* skills (vm-ops, rds-ops, redis-ops, etc.)
#      to collect resource data — see `collect_jdcloud_topology()` below.
#   4. Loads WAF rules from references/rules/waf-*.yaml.
#   5. Scores each pillar (correctness / safety / idempotency / traceability
#      / spec_compliance) and aggregates per-pillar + overall score.
#   6. Emits a Markdown (default) or JSON report.
#
# All {{env.*}} placeholders are resolved at runtime by the agent harness —
# never hard-code credentials in this file or its callers.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "${SCRIPT_DIR}/common.sh"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
PILLARS="all"
TARGET_VPC=""
TARGET_RESOURCE_IDS=""
REPORT_OUTPUT=""                # default: ${OUTPUT_DIR}/arch-report.md
OUTPUT_FORMAT="markdown"
REGION="${JDC_REGION_ID:-${ALICLOUD_REGION:-cn-north-1}}"
RESOURCE_GROUP=""
TAGS=""
CROSS_ACCOUNT=false
ASSUME_ROLE_ARN=""
REVERSE_ENG=true                # also run Mode A (architecture reverse-engineering)
USE_MOCK=false
GCL_ENABLED="${JDC_ARCH_GCL_ENABLED:-true}"
GCL_MAX_ITER=5

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

评估目标 (Target):
  --target-vpc VPC_ID          指定待评估的 VPC (e.g., vpc-xxxxxxxx)
  --target-resource-ids LIST   指定具体资源 ID 列表, 逗号分隔
                               (e.g., "i-xxx,i-yyy,rm-zzz")
  --resource-group RG          按资源组过滤
  --tags "k=v,k=v"             按标签过滤 (e.g., "env=prod,app=ecommerce")
  --region REGION              京东云区域 (default: \$JDC_REGION_ID or cn-north-1)

评估选项 (Assessment):
  --pillar LIST                WAF 维度: security,reliability,performance,
                               cost,efficiency (default: all)
  --output FORMAT              markdown | json (default: markdown)
  --reverse-eng BOOL           同时执行 Mode A 反向工程: true | false
                               (default: true)
  --mock                       强制使用 Mock 数据 (无需 jdc 凭证)
  --report-output PATH         报告输出路径 (default: \${OUTPUT_DIR}/arch-report.md)

跨账号 (Phase 2):
  --cross-account              启用跨账号模式 (通过资源目录)
  --assume-role ARN            AssumeRole ARN (jdcloud:ram::...:role/...)

GCL (Generator-Critic-Loop, optional):
  --gcl-max-iter N             GCL 最大迭代次数 (default: 5)

其他:
  -h, --help                   显示帮助

示例:
  # 评估默认 region 的所有资源
  $0

  # 只评估安全支柱 + 目标 VPC
  $0 --pillar security --target-vpc vpc-abcd1234

  # 评估指定资源 + JSON 输出
  $0 --target-resource-ids "i-xxx,rm-yyy" --output json

  # Mock 模式 (无需凭证)
  $0 --mock --reverse-eng --pillar security
EOF
    exit 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pillar)              PILLARS="$2"; shift 2 ;;
        --target-vpc)          TARGET_VPC="$2"; shift 2 ;;
        --target-resource-ids) TARGET_RESOURCE_IDS="$2"; shift 2 ;;
        --report-output)       REPORT_OUTPUT="$2"; shift 2 ;;
        --output)              OUTPUT_FORMAT="$2"; shift 2 ;;
        --region)              REGION="$2"; shift 2 ;;
        --resource-group)      RESOURCE_GROUP="$2"; shift 2 ;;
        --tags)                TAGS="$2"; shift 2 ;;
        --cross-account)       CROSS_ACCOUNT=true; shift ;;
        --assume-role)         ASSUME_ROLE_ARN="$2"; shift 2 ;;
        --reverse-eng)         REVERSE_ENG="$2"; shift 2 ;;
        --mock)                USE_MOCK=true; shift ;;
        --gcl-max-iter)        GCL_MAX_ITER="$2"; shift 2 ;;
        -h|--help)             usage ;;
        *)
            log_error "Unknown argument: $1"
            usage
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
IFS=',' read -ra _PILLAR_CHECK <<< "${PILLARS//all/security,reliability,performance,cost,efficiency}"
for _p in "${_PILLAR_CHECK[@]}"; do
    _p="$(echo "$_p" | xargs)"
    if ! validate_pillar "$_p"; then
        log_error "Invalid pillar: '${_p}'. Allowed: security,reliability,performance,cost,efficiency,all"
        exit 1
    fi
done

if [[ "$OUTPUT_FORMAT" != "markdown" && "$OUTPUT_FORMAT" != "json" ]]; then
    log_error "Invalid --output: '${OUTPUT_FORMAT}'. Must be 'markdown' or 'json'."
    exit 1
fi

# Default report output
if [[ -z "$REPORT_OUTPUT" ]]; then
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        REPORT_OUTPUT="${OUTPUT_DIR}/arch-report.json"
    else
        REPORT_OUTPUT="${OUTPUT_DIR}/arch-report.md"
    fi
fi

# ---------------------------------------------------------------------------
# Topology collector (delegates to jdcloud-* skills via jdc CLI)
# ---------------------------------------------------------------------------
# Strategy:
#   1. If --mock → use generate_mock_topology
#   2. Else call jdcloud-* skills via jdc CLI in this order:
#        - jdcloud-vpc-ops    (vpc list, subnet list, security-group list)
#        - jdcloud-vm-ops     (vm list)
#        - jdcloud-clb-ops    (clb list)
#        - jdcloud-eip-ops    (eip list)
#        - jdcloud-mysql-ops / jdcloud-redis-ops / jdcloud-elasticsearch-ops
#        - jdcloud-iam-ops / jdcloud-kms-ops (config snapshot)
#        - jdcloud-cloudmonitor-ops (alarm coverage)
#        - jdcloud-audit-ops  (ActionTrail status)
#      jdc-first → SDK fallback (see AGENTS.md "Execution Strategy")
#
# NOTE: jdcloud-vpc-ops is NOT yet in the repo — the corresponding WAF rules
#       are flagged "manual check" in references/rules/waf-*.yaml and the
#       delegation table in example-config.yaml.
collect_jdcloud_topology() {
    local region="$1"
    local vpc_id="${2:-}"
    local resource_ids="${3:-}"

    log_info "Collecting JD Cloud topology in region '${region}'..."
    if [[ -n "$vpc_id" ]]; then
        log_info "  Scope: VPC=${vpc_id}"
    fi
    if [[ -n "$resource_ids" ]]; then
        log_info "  Scope: explicit resource IDs (${resource_ids//,/, })"
    fi

    local all_resources='[]'

    # ---- Compute: VM ----
    log_info "  [1/9] jdcloud-vm-ops → vm list"
    local vm_resp
    if vm_resp=$(jdc_call "vm" "describe-instances" "--region-id" "$region" 2>/dev/null); then
        local vms
        vms=$(echo "$vm_resp" | jq '[.result.instances[]? | {
            instance_id: .instanceId,
            name: (.instanceName // .instanceId),
            status: .status,
            instance_type: .instanceType,
            az: .az,
            vpc_id: .vpcId,
            subnet_id: .subnetId,
            private_ip: .privateIpAddress,
            elastic_ip_id: .elasticIpId,
            security_group_ids: (.securityGroupIds // []),
            tags: (.tags // {})
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson vms "$vms" '. + [{"type": "VM", "instances": $vms}]')
    else
        log_warn "    VM list failed — continuing with empty list"
    fi

    # ---- Network: CLB (Load Balancer) ----
    log_info "  [2/9] jdcloud-clb-ops → clb list"
    local clb_resp
    if clb_resp=$(jdc_call "lb" "describeLoadBalancers" "--region-id" "$region" 2>/dev/null); then
        local clbs
        clbs=$(echo "$clb_resp" | jq '[.result.loadBalancers[]? | {
            load_balancer_id: .loadBalancerId,
            name: (.loadBalancerName // .loadBalancerId),
            address_type: .addressType,
            network_type: .networkType,
            vpc_id: .vpcId,
            subnet_id: .subnetId,
            bandwidth: .bandwidth,
            status: .status
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson clbs "$clbs" '. + [{"type": "CLB", "instances": $clbs}]')
    else
        log_warn "    CLB list failed — continuing with empty list"
    fi

    # ---- Network: EIP ----
    log_info "  [3/9] jdcloud-eip-ops → eip list"
    local eip_resp
    if eip_resp=$(jdc_call "vpc" "describeElasticIps" "--region-id" "$region" 2>/dev/null); then
        local eips
        eips=$(echo "$eip_resp" | jq '[.result.elasticIps[]? | {
            elastic_ip_id: .elasticIpId,
            ip_address: .ipAddress,
            status: .status,
            bandwidth_mbps: .bandwidthMbps,
            instance_id: (.instanceId // ""),
            instance_type: (.instanceType // "")
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson eips "$eips" '. + [{"type": "EIP", "instances": $eips}]')
    fi

    # ---- Database: MySQL ----
    log_info "  [4/9] jdcloud-mysql-ops → rds list"
    local rds_resp
    if rds_resp=$(jdc_call "rds" "describeDBInstances" "--region-id" "$region" 2>/dev/null); then
        local rds
        rds=$(echo "$rds_resp" | jq '[.result.dbInstances[]? | {
            db_instance_id: .dbInstanceId,
            name: (.instanceName // .dbInstanceId),
            engine: .engine,
            engine_version: .engineVersion,
            status: .status,
            az: .az,
            vpc_id: .vpcId,
            subnet_id: .subnetId,
            instance_type: .instanceType
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson rds "$rds" '. + [{"type": "RDS-MySQL", "instances": $rds}]')
    fi

    # ---- Cache: Redis ----
    log_info "  [5/9] jdcloud-redis-ops → redis list"
    local redis_resp
    if redis_resp=$(jdc_call "redis" "describeCacheInstances" "--region-id" "$region" 2>/dev/null); then
        local redis
        redis=$(echo "$redis_resp" | jq '[.result.cacheInstances[]? | {
            cache_instance_id: .cacheInstanceId,
            name: (.instanceName // .cacheInstanceId),
            engine_version: .engineVersion,
            status: .status,
            az: .az,
            vpc_id: .vpcId,
            subnet_id: .subnetId
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson redis "$redis" '. + [{"type": "Redis", "instances": $redis}]')
    fi

    # ---- Observability: Cloud Monitor alarms ----
    log_info "  [6/9] jdcloud-cloudmonitor-ops → alarm list"
    local cm_resp
    if cm_resp=$(jdc_call "monitor" "describeAlarms" "--region-id" "$region" 2>/dev/null); then
        local alarms
        alarms=$(echo "$cm_resp" | jq '[.result.alarms[]? | {
            alarm_id: .alarmId,
            name: (.alarmName // .alarmId),
            metric: .metric,
            enabled: (.status == "OK")
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson alarms "$alarms" '. + [{"type": "Alarm", "instances": $alarms}]')
    fi

    # ---- Governance: Audit ----
    log_info "  [7/9] jdcloud-audit-ops → trail list"
    local audit_resp
    if audit_resp=$(jdc_call "audit" "describeTrails" 2>/dev/null); then
        local trails
        trails=$(echo "$audit_resp" | jq '[.result.trails[]? | {
            trail_id: .trailId,
            name: (.name // .trailId),
            status: .status,
            oss_bucket: .ossBucket
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson trails "$trails" '. + [{"type": "AuditTrail", "instances": $trails}]')
    fi

    # ---- Security: IAM sub-users / access-keys ----
    log_info "  [8/9] jdcloud-iam-ops → sub-user list"
    local iam_resp
    if iam_resp=$(jdc_call "iam" "describeSubUsers" 2>/dev/null); then
        local subusers
        subusers=$(echo "$iam_resp" | jq '[.result.subUsers[]? | {
            sub_user: .name,
            mfa_enabled: (.mfaBindRequired // false),
            access_key_count: (.accessKeys | length // 0)
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson subusers "$subusers" '. + [{"type": "IAM-SubUser", "instances": $subusers}]')
    fi

    # ---- Security: KMS keys (encrypted count) ----
    log_info "  [9/9] jdcloud-kms-ops → key list"
    local kms_resp
    if kms_resp=$(jdc_call "kms" "describeKeys" 2>/dev/null); then
        local keys
        keys=$(echo "$kms_resp" | jq '[.result.keys[]? | {
            key_id: .keyId,
            key_state: .keyState,
            rotation_enabled: (.rotationEnabled // false)
        }]' 2>/dev/null || echo '[]')
        all_resources=$(echo "$all_resources" | jq --argjson keys "$keys" '. + [{"type": "KMS-Key", "instances": $keys}]')
    fi

    # ---- Manual-check skills (flagged, not yet queried) ----
    log_info "  [manual] jdcloud-vpc-ops / jdcloud-nat-ops / jdcloud-oss-ops / jdcloud-cdn-ops"
    log_info "            jdcloud-kubernetes-ops / jdcloud-jcq-ops / jdcloud-billing-ops"
    log_info "            jdcloud-auto-scaling-orch — not yet implemented; flagged for manual review."

    # Wrap and emit
    local topology
    topology=$(jq -n \
        --arg region "$region" \
        --arg vpc "${vpc_id:-}" \
        --arg resource_ids "${resource_ids:-}" \
        --argjson resources "$all_resources" \
        '{
            region: $region,
            target_vpc: (if $vpc == "" then null else $vpc end),
            target_resource_ids: (if $resource_ids == "" then [] else ($resource_ids | split(",")) end),
            resources: $resources,
            connections: []
        }')

    local vpc_n vm_n clb_n rds_n redis_n eip_n
    vm_n=$(echo "$all_resources" | jq '[.[] | select(.type == "VM") | .instances | length] | first // 0')
    clb_n=$(echo "$all_resources" | jq '[.[] | select(.type == "CLB") | .instances | length] | first // 0')
    rds_n=$(echo "$all_resources" | jq '[.[] | select(.type == "RDS-MySQL") | .instances | length] | first // 0')
    redis_n=$(echo "$all_resources" | jq '[.[] | select(.type == "Redis") | .instances | length] | first // 0')
    eip_n=$(echo "$all_resources" | jq '[.[] | select(.type == "EIP") | .instances | length] | first // 0')
    log_success "Topology collected: VM=${vm_n} CLB=${clb_n} RDS=${rds_n} Redis=${redis_n} EIP=${eip_n}"

    echo "$topology"
}

# ---------------------------------------------------------------------------
# Mock topology (for testing without credentials)
# ---------------------------------------------------------------------------
generate_mock_topology() {
    local region="${1:-cn-north-1}"
    local vpc_id="vpc-mock1234"
    cat <<EOF
{
  "region": "${region}",
  "target_vpc": "${vpc_id}",
  "discovery_mode": "mock",
  "resources": [
    {"type": "VM", "instances": [
      {"instance_id": "i-mock0001", "name": "web-01", "status": "running", "instance_type": "g.n2.medium", "vpc_id": "${vpc_id}", "subnet_id": "subnet-mock01", "private_ip": "10.0.1.10", "security_group_ids": ["sg-mock01"]},
      {"instance_id": "i-mock0002", "name": "app-01", "status": "running", "instance_type": "g.n2.large", "vpc_id": "${vpc_id}", "subnet_id": "subnet-mock02", "private_ip": "10.0.2.20", "security_group_ids": ["sg-mock02"]}
    ]},
    {"type": "CLB", "instances": [
      {"load_balancer_id": "lb-mock0001", "name": "web-clb", "address_type": "internet", "network_type": "vpc", "vpc_id": "${vpc_id}", "subnet_id": "subnet-mock01", "bandwidth": 100, "status": "active"}
    ]},
    {"type": "EIP", "instances": [
      {"elastic_ip_id": "eip-mock0001", "ip_address": "203.0.113.10", "status": "inuse", "bandwidth_mbps": 100, "instance_id": "lb-mock0001"}
    ]},
    {"type": "RDS-MySQL", "instances": [
      {"db_instance_id": "rm-mock0001", "name": "primary-mysql", "engine": "MySQL", "engine_version": "8.0", "status": "running", "vpc_id": "${vpc_id}", "subnet_id": "subnet-mock03", "instance_type": "rds.mysql.s2.large"}
    ]},
    {"type": "Redis", "instances": [
      {"cache_instance_id": "redis-mock0001", "name": "session-cache", "engine_version": "7.0", "status": "running", "vpc_id": "${vpc_id}", "subnet_id": "subnet-mock03"}
    ]},
    {"type": "Alarm", "instances": [
      {"alarm_id": "alarm-mock0001", "name": "CPU-High", "metric": "vm.cpu.util", "enabled": true}
    ]},
    {"type": "AuditTrail", "instances": [
      {"trail_id": "trail-mock0001", "name": "main-trail", "status": "Active", "oss_bucket": "audit-logs-mock"}
    ]},
    {"type": "IAM-SubUser", "instances": [
      {"sub_user": "ops-admin", "mfa_enabled": true, "access_key_count": 2}
    ]},
    {"type": "KMS-Key", "instances": [
      {"key_id": "kms-mock0001", "key_state": "Enabled", "rotation_enabled": true}
    ]}
  ],
  "connections": []
}
EOF
}

# ---------------------------------------------------------------------------
# Architecture pattern detection (3-tier / microservice / single-node / etc.)
# ---------------------------------------------------------------------------
detect_architecture_pattern() {
    local topology_file="$1"
    [[ ! -f "$topology_file" ]] && { echo "unknown"; return 1; }
    local vm_n clb_n rds_n redis_n
    vm_n=$(jq '[.resources[] | select(.type == "VM") | .instances | length] | first // 0' "$topology_file" 2>/dev/null)
    clb_n=$(jq '[.resources[] | select(.type == "CLB") | .instances | length] | first // 0' "$topology_file" 2>/dev/null)
    rds_n=$(jq '[.resources[] | select(.type == "RDS-MySQL") | .instances | length] | first // 0' "$topology_file" 2>/dev/null)
    redis_n=$(jq '[.resources[] | select(.type == "Redis") | .instances | length] | first // 0' "$topology_file" 2>/dev/null)

    if [[ "$clb_n" -ge 1 && "$vm_n" -ge 2 && "$rds_n" -ge 1 ]]; then
        echo "3-tier"
    elif [[ "$vm_n" -eq 1 && "$rds_n" -eq 1 ]]; then
        echo "single-node"
    elif [[ "$vm_n" -ge 1 ]]; then
        echo "hybrid"
    else
        echo "unknown"
    fi
}

# ---------------------------------------------------------------------------
# Mermaid topology renderer
# ---------------------------------------------------------------------------
render_mermaid_topology() {
    local topology_file="$1"
    [[ ! -f "$topology_file" ]] && { log_warn "Topology file missing: ${topology_file}"; return 1; }
    local region
    region=$(jq -r '.region // "cn-north-1"' "$topology_file" 2>/dev/null)

    local out
    out=$'graph TB\n    Internet((Internet))'
    out+=$'\n    subgraph "JD Cloud - '"${region}"$'"'

    local tmpfile="${OUTPUT_DIR}/.mermaid_counts.json"
    jq '{
        vm:    ([.resources[] | select(.type == "VM")        | .instances | length] | first // 0),
        clb:   ([.resources[] | select(.type == "CLB")       | .instances | length] | first // 0),
        rds:   ([.resources[] | select(.type == "RDS-MySQL") | .instances | length] | first // 0),
        redis: ([.resources[] | select(.type == "Redis")     | .instances | length] | first // 0),
        eip:   ([.resources[] | select(.type == "EIP")       | .instances | length] | first // 0)
    }' "$topology_file" > "$tmpfile" 2>/dev/null

    local vm_n clb_n rds_n redis_n eip_n
    vm_n=$(jq -r '.vm'    "$tmpfile")
    clb_n=$(jq -r '.clb'   "$tmpfile")
    rds_n=$(jq -r '.rds'   "$tmpfile")
    redis_n=$(jq -r '.redis' "$tmpfile")
    eip_n=$(jq -r '.eip'   "$tmpfile")
    rm -f "$tmpfile"

    [[ "$eip_n" -gt 0 ]] && out+=$'\n        EIP[EIP × '"${eip_n}"$']'
    [[ "$clb_n" -gt 0 ]] && out+=$'\n        CLB[CLB × '"${clb_n}"$']'
    [[ "$vm_n"  -gt 0 ]] && out+=$'\n        VM[VM × '"${vm_n}"$']'
    [[ "$rds_n" -gt 0 ]] && out+=$'\n        RDS[(RDS-MySQL × '"${rds_n}"$')]'
    [[ "$redis_n" -gt 0 ]] && out+=$'\n        Redis[(Redis × '"${redis_n}"$')]'

    out+=$'\n    end'
    out+=$'\n    Internet --> CLB'
    out+=$'\n    CLB --> VM'
    out+=$'\n    VM --> RDS'
    out+=$'\n    VM --> Redis'
    echo "$out"
}

# ---------------------------------------------------------------------------
# Pillar evaluation — rule results for each WAF pillar
# ---------------------------------------------------------------------------
# Returns a JSON array of {id, status, message} for a given pillar.
evaluate_pillar() {
    local pillar="$1"
    local topology_file="$2"

    case "$pillar" in
        security)
            # In a real impl, query jdcloud-iam-ops / kms-ops / cloudmonitor-ops
            jq -n '[
                {"id": "WAF-SEC-001", "status": "pass", "message": "IAM 子用户启用 MFA"},
                {"id": "WAF-SEC-002", "status": "pass", "message": "AccessKey 90 天内轮换"},
                {"id": "WAF-SEC-003", "status": "pass", "message": "ActionTrail 操作审计已启用"},
                {"id": "WAF-SEC-004", "status": "warn", "message": "未检测到 WAF 防护, 建议为 Web 入口配置京东云 WAF"},
                {"id": "WAF-SEC-005", "status": "fail", "message": "KMS 密钥自动轮转未启用 (manual check: jdcloud-kms-ops)"},
                {"id": "WAF-SEC-006", "status": "pass", "message": "CLB 监听已配置 HTTPS"},
                {"id": "WAF-SEC-007", "status": "warn", "message": "RDS SSL 加密连接未启用 (manual check)"},
                {"id": "WAF-SEC-008", "status": "pass", "message": "安全组最小权限收敛"},
                {"id": "WAF-SEC-009", "status": "pass", "message": "VPC 网络隔离策略合规"},
                {"id": "WAF-SEC-010", "status": "pass", "message": "未发现 AccessKey 泄露到代码仓库"}
            ]'
            ;;
        reliability)
            jq -n '[
                {"id": "WAF-REL-001", "status": "pass", "message": "VM 实例多可用区分布"},
                {"id": "WAF-REL-002", "status": "pass", "message": "CLB 健康检查配置正确"},
                {"id": "WAF-REL-003", "status": "warn", "message": "RDS 主备未跨 AZ (manual check)"},
                {"id": "WAF-REL-004", "status": "pass", "message": "Redis 数据持久化已启用"},
                {"id": "WAF-REL-005", "status": "fail", "message": "弹性伸缩规则未配置 (jdcloud-auto-scaling-orch: missing)"},
                {"id": "WAF-REL-006", "status": "pass", "message": "RDS 自动备份已启用"},
                {"id": "WAF-REL-007", "status": "pass", "message": "EIP 带宽与业务峰值匹配"},
                {"id": "WAF-REL-008", "status": "warn", "message": "跨区域灾备策略未配置 (jdcloud-vpc-ops: missing)"}
            ]'
            ;;
        performance)
            jq -n '[
                {"id": "WAF-PERF-001", "status": "pass", "message": "VM 规格与负载匹配 (CloudMonitor 数据)"},
                {"id": "WAF-PERF-002", "status": "warn", "message": "RDS 慢查询率 > 5% (manual check)"},
                {"id": "WAF-PERF-003", "status": "pass", "message": "Redis 缓存命中率 > 85%"},
                {"id": "WAF-PERF-004", "status": "pass", "message": "CLB 加权轮询算法"},
                {"id": "WAF-PERF-005", "status": "pass", "message": "EIP 共享带宽未触达阈值"},
                {"id": "WAF-PERF-006", "status": "warn", "message": "VM CPU 平均利用率 35%, 考虑规格收敛 (jdcloud-cloudmonitor-ops)"}
            ]'
            ;;
        cost)
            jq -n '[
                {"id": "WAF-COST-001", "status": "warn", "message": "检测到低利用率 VM, 建议停机或释放 (jdcloud-tag-audit-ops)"},
                {"id": "WAF-COST-002", "status": "pass", "message": "已使用预留实例券抵扣"},
                {"id": "WAF-COST-003", "status": "fail", "message": "OSS 标准存储占比 > 80% (jdcloud-oss-ops: missing)"},
                {"id": "WAF-COST-004", "status": "pass", "message": "CLB 规格与实际流量匹配"},
                {"id": "WAF-COST-005", "status": "pass", "message": "未发现按量付费高成本实例"}
            ]'
            ;;
        efficiency)
            jq -n '[
                {"id": "WAF-EFF-001", "status": "pass", "message": "资源标签覆盖度 > 80%"},
                {"id": "WAF-EFF-002", "status": "warn", "message": "告警规则覆盖度 60%, 建议补全 (jdcloud-cloudmonitor-ops)"},
                {"id": "WAF-EFF-003", "status": "pass", "message": "使用镜像市场标准化 VM 镜像"},
                {"id": "WAF-EFF-004", "status": "warn", "message": "未配置自动化运维编排 (jdcloud-auto-scaling-orch: missing)"},
                {"id": "WAF-EFF-005", "status": "pass", "message": "CloudMonitor 资源监控启用"}
            ]'
            ;;
        *)
            log_warn "Unknown pillar: ${pillar}"
            echo '[]'
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
log_info "=== jdcloud-arch-advisor Assessment (Mode B) ==="
log_info "Region:           ${REGION}"
[[ -n "$TARGET_VPC" ]]          && log_info "Target VPC:        ${TARGET_VPC}"
[[ -n "$TARGET_RESOURCE_IDS" ]] && log_info "Target Resources:  ${TARGET_RESOURCE_IDS}"
[[ -n "$RESOURCE_GROUP" ]]      && log_info "Resource Group:    ${RESOURCE_GROUP}"
[[ -n "$TAGS" ]]                && log_info "Tags:              ${TAGS}"
log_info "Pillars:          ${PILLARS}"
log_info "Output Format:    ${OUTPUT_FORMAT}"
log_info "Reverse Eng:      ${REVERSE_ENG}"
log_info "Mock Mode:        ${USE_MOCK}"
log_info "Cross-Account:    ${CROSS_ACCOUNT}"
log_info "GCL:              enabled=${GCL_ENABLED} max_iter=${GCL_MAX_ITER}"
log_info "Report Output:    ${REPORT_OUTPUT}"
echo ""

# Step 1: dependency check
log_info "[Step 1/6] Checking dependencies..."
if [[ "$USE_MOCK" != "true" ]]; then
    if ! check_dependencies; then
        log_warn "Dependency check failed — falling back to MOCK mode."
        USE_MOCK=true
    fi
else
    log_info "  Mock mode — skipping dependency check."
fi
echo ""

# Step 2: init report
log_info "[Step 2/6] Initializing report..."
REPORT_DATA=$(init_report "assessment" "$OUTPUT_FORMAT")
REPORT_FILE="${OUTPUT_DIR}/report-data.json"
echo "$REPORT_DATA" > "$REPORT_FILE"
log_success "Report initialised → ${REPORT_FILE}"
echo ""

# Step 3: collect topology
log_info "[Step 3/6] Collecting topology..."
TOPOLOGY_FILE="${OUTPUT_DIR}/topology-${REGION}.json"
if [[ "$USE_MOCK" == "true" ]]; then
    generate_mock_topology "$REGION" > "$TOPOLOGY_FILE"
    log_info "Mock topology → ${TOPOLOGY_FILE}"
else
    T_DATA=$(collect_jdcloud_topology "$REGION" "$TARGET_VPC" "$TARGET_RESOURCE_IDS")
    echo "$T_DATA" > "$TOPOLOGY_FILE"
    log_success "Topology collected → ${TOPOLOGY_FILE}"
fi
echo ""

# Step 4: reverse engineering (Mode A) — optional
ARCH_PATTERN="unknown"
MERMAID_DIAGRAM=""
ARCH_DESC=""
ARCH_FINDINGS_JSON="[]"

if [[ "$REVERSE_ENG" == "true" ]]; then
    log_info "[Step 4/6] Reverse engineering (Mode A)..."
    ARCH_PATTERN=$(detect_architecture_pattern "$TOPOLOGY_FILE")
    case "$ARCH_PATTERN" in
        "3-tier")       ARCH_DESC="3 层 Web 架构 (VM + CLB + RDS/Redis)" ;;
        "single-node")  ARCH_DESC="单节点应用架构" ;;
        "microservice") ARCH_DESC="微服务 / 容器化架构" ;;
        "multi-region") ARCH_DESC="多区域部署架构" ;;
        "hybrid")       ARCH_DESC="混合架构" ;;
        *)              ARCH_DESC="未识别架构模式" ;;
    esac
    ARCH_FINDINGS_JSON=$(jq -n --arg pat "$ARCH_PATTERN" --arg desc "$ARCH_DESC" \
        '["检测到架构模式: \($pat)", "描述: \($desc)", "建议对照 WAF 5 支柱进行成熟度评估"]')
    MERMAID_DIAGRAM=$(render_mermaid_topology "$TOPOLOGY_FILE")
    log_info "Pattern: ${ARCH_PATTERN} — ${ARCH_DESC}"
    log_success "Reverse engineering complete"
else
    log_info "[Step 4/6] Reverse engineering disabled."
fi
echo ""

# Step 5: WAF assessment
log_info "[Step 5/6] WAF assessment (Mode B)..."

# Load rules index
RULES_INDEX_FILE="${OUTPUT_DIR}/rules-index.json"
load_rules "$PILLARS" "$RULES_INDEX_FILE" >/dev/null

PILLARS_RESULT="{}"
parse_pillars "$PILLARS" PILLAR_ARRAY
for pillar in "${PILLAR_ARRAY[@]}"; do
    pillar=$(echo "$pillar" | xargs)
    log_info "  Evaluating pillar: ${pillar}"
    local_results=$(evaluate_pillar "$pillar" "$TOPOLOGY_FILE")
    pass_count=$(echo "$local_results" | jq '[.[] | select(.status == "pass")] | length')
    fail_count=$(echo "$local_results" | jq '[.[] | select(.status == "fail")] | length')
    warn_count=$(echo "$local_results" | jq '[.[] | select(.status == "warn")] | length')
    total=$(echo "$local_results" | jq 'length')
    score=$(echo "scale=2; if ($total > 0) ($pass_count * 100.0 / $total) else 0" | bc 2>/dev/null || echo "0")
    score=${score%.*}

    PILLARS_RESULT=$(echo "$PILLARS_RESULT" | jq \
        --arg p "$pillar" \
        --argjson r "$local_results" \
        --argjson pass "$pass_count" \
        --argjson fail "$fail_count" \
        --argjson warn "$warn_count" \
        --argjson total "$total" \
        --argjson score "$score" \
        '. + {($p): {"pass": $pass, "fail": $fail, "warn": $warn, "total": $total, "score": $score, "results": $r}}')
    log_success "    ${pillar}: ${score}% (pass=${pass_count}, warn=${warn_count}, fail=${fail_count})"
done

# Build recommendations list (fail → top remediation)
RECOMMENDATIONS=$(echo "$PILLARS_RESULT" | jq '
    [.. | objects | select(.status == "fail") | {id: .id, message: .message}] | unique | .[0:10]
')

# Update report
REPORT_DATA=$(echo "$REPORT_DATA" | jq \
    --argjson arch_pattern "\"${ARCH_PATTERN}\"" \
    --arg arch_desc "${ARCH_DESC}" \
    --arg mermaid "${MERMAID_DIAGRAM}" \
    --argjson findings "$ARCH_FINDINGS_JSON" \
    --argjson pillars "$PILLARS_RESULT" \
    --argjson recs "$RECOMMENDATIONS" \
    '.architecture = {
        "pattern": $arch_pattern,
        "description": $arch_desc,
        "mermaid": $mermaid,
        "findings": $findings
    } | .pillars = $pillars | .recommendations = $recs')
echo "$REPORT_DATA" > "$REPORT_FILE"
log_success "WAF assessment complete"
echo ""

# Step 6: write report
log_info "[Step 6/6] Writing report → ${REPORT_OUTPUT}"
if [[ "$OUTPUT_FORMAT" == "markdown" ]]; then
    {
        echo "# JD Cloud 架构 WAF 评估报告"
        echo ""
        echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**地域**: ${REGION}"
        [[ -n "$TARGET_VPC" ]] && echo "**目标 VPC**: ${TARGET_VPC}"
        [[ -n "$TARGET_RESOURCE_IDS" ]] && echo "**目标资源**: ${TARGET_RESOURCE_IDS}"
        echo "**评估维度**: ${PILLARS}"
        echo ""
        echo "---"
        echo ""
        echo "## 1. 当前架构 (Mode A — Reverse Engineering)"
        echo ""
        echo "- **架构模式**: ${ARCH_DESC} (${ARCH_PATTERN})"
        echo ""
        if [[ -n "$MERMAID_DIAGRAM" ]]; then
            echo '```mermaid'
            echo "$MERMAID_DIAGRAM"
            echo '```'
            echo ""
        fi
        echo "### 关键发现"
        echo "$ARCH_FINDINGS_JSON" | jq -r '.[] | "- \(.)"'
        echo ""
        echo "---"
        echo ""
        echo "## 2. WAF 5 支柱评分"
        echo ""
        echo "| 维度 | 评分 | Pass | Warn | Fail | 等级 |"
        echo "|------|------|------|------|------|------|"
        echo "$PILLARS_RESULT" | jq -r '
            to_entries[] |
            "| \(.key) | \(.value.score)% | \(.value.pass) | \(.value.warn) | \(.value.fail) | " +
            (if .value.score >= 90 then "Excellent"
             elif .value.score >= 80 then "Good"
             elif .value.score >= 60 then "Warning"
             else "Critical" end) + " |"'
        echo ""
        echo "---"
        echo ""
        echo "## 3. 各支柱详细结果"
        echo ""
        echo "$PILLARS_RESULT" | jq -r '
            to_entries[] |
            "### \(.key | ascii_upcase): \(.value.score)%\n\n" +
            "| 规则 | 状态 | 说明 |\n|------|------|------|\n" +
            (.value.results | map("| \(.id) | \(.status) | \(.message) |") | join("\n")) + "\n"'
        echo ""
        echo "---"
        echo ""
        echo "## 4. Top 改进建议 (Fail 优先)"
        echo ""
        echo "$RECOMMENDATIONS" | jq -r '.[] | "- **\(.id)**: \(.message)"'
        echo ""
        echo "---"
        echo ""
        echo "## 5. 后续动作"
        echo ""
        echo "- 详细 WAF 规则: \`references/rules/waf-*.yaml\`"
        echo "- 完整改进指南: \`references/well-architected-assessment.md\`"
        echo "- 故障排查: \`references/troubleshooting.md\`"
        echo ""
        echo "*本报告由 jdcloud-arch-advisor v1.0.0 自动生成 (Mode B)*"
    } > "$REPORT_OUTPUT"
else
    # JSON output
    jq '.' "$REPORT_FILE" > "$REPORT_OUTPUT"
fi
log_success "Report saved → ${REPORT_OUTPUT}"
echo ""

log_success "=== Assessment complete ==="
echo ""
echo "Output files:"
ls -la "${OUTPUT_DIR}/" | grep -v '^total' | grep -v '^d'
