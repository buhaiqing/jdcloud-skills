# CLI — JD Cloud API Gateway (`jdc ag` / `jdc apigateway`)

> **⚠️ 当前状态**：`jdc apigateway` / `jdc ag` 命令在当前锁定版本中**未验证**。`jdcloud-apigateway-ops` Skill 官方定位为 **SDK-only**（见 `SKILL.md` 中 `cli_applicability: sdk-only`）。
> 以下命令均为**期望语法示例**，实际执行前请确认 `jdc` 版本已提供该产品组。若命令返回 `invalid choice: 'apigateway'` 或 `invalid choice: 'ag'`，请改用 [API & SDK Usage](./api-sdk-usage.md) 的 Python SDK 路径。

## Install and config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** `jdc` CLI 仅从 `~/.jdc/config` INI 文件读取凭证，**不**使用 `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` 环境变量。
- 沙箱环境：将 `HOME` 重定向到可写目录并预创建配置文件（见 SKILL.md "Critical jdc CLI Behavioral Notes"）。

## Conventions (agent execution)

- **`--output json` 是顶层参数**，必须放在子命令**之前**：`jdc --output json ag <command> ...`
- `--no-interactive` 在 `jdc` CLI 中**不存在**——所有命令默认非交互式；**省略**该标志。
- API Gateway 在 `jdc` 中**预期命令前缀**为 `apigateway` 或短别名 `ag`。如 `jdc ag create-api-group ...`。
- 所有 list 类命令均支持 `--page-number` / `--page-size` 分页参数；`--page-size` 上限通常为 100。
- 所有命令**必须**显式传 `--region-id`；无默认 region 继承。
- JSON 响应路径以实际 `jdc` 输出为准——可能与原生 API 略有差异，需首次运行后再固化路径。

## CLI vs API Coverage Gap

| 操作 (API / SDK) | `jdc` 是否可用? | 备注 |
|------------------|----------------|------|
| CreateApiGroup | 未验证（期望） | `jdc ag create-api-group` |
| DeleteApiGroup | 未验证（期望） | `jdc ag delete-api-group` |
| DescribeApiGroup | 未验证（期望） | `jdc ag describe-api-group` |
| DescribeApiGroups (list) | 未验证（期望） | `jdc ag describe-api-groups` |
| CreateApi | 未验证（期望） | `jdc ag create-api` |
| DeleteApi | 未验证（期望） | `jdc ag delete-api` |
| ModifyApi | 未验证（期望） | `jdc ag modify-api` |
| DescribeApi | 未验证（期望） | `jdc ag describe-api` |
| DescribeApis (list) | 未验证（期望） | `jdc ag describe-apis` |
| DeployApi | 未验证（期望） | `jdc ag deploy-api` |
| UndeployApi | 未验证（期望） | `jdc ag undeploy-api` |
| DescribeDeployments | 未验证（期望） | `jdc ag describe-deployments` |
| CreateThrottlingPolicy | 未验证（期望） | `jdc ag create-throttling-policy` |
| DeleteThrottlingPolicy | 未验证（期望） | `jdc ag delete-throttling-policy` |
| DescribeThrottlingPolicies | 未验证（期望） | `jdc ag describe-throttling-policies` |
| BindThrottlingPolicy | 未验证（期望） | `jdc ag bind-throttling-policy` |
| UnbindThrottlingPolicy | 未验证（期望） | `jdc ag unbind-throttling-policy` |
| DescribeApiThrottling | 未验证（期望） | `jdc ag describe-api-throttling` |
| 查询 API 调用日志 / 指标 | 未验证 | 可能在 `monitor` / `logservice` 产品组而非 `ag` |

> **结论**：截至 `jdcloud_cli` 当前锁定版本，API Gateway 仍为 SDK-only 产品；上述 CLI 命令均为未来版本的期望语法。在命令实际不可用时，Agent **必须**回退到 [api-sdk-usage.md](./api-sdk-usage.md) 的 Python SDK。

## Command map

### API Group 操作

| 目标 | `jdc` 调用示例 | 备注 |
|------|---------------|------|
| 创建 API 分组 | <code># 期望语法示例<br>jdc --output json ag create-api-group --region-id cn-north-1 --group-name v1-service --description "created via cli"</code> | `--output json` 必须在子命令前 |
| 查询单个分组 | <code>jdc --output json ag describe-api-group --region-id cn-north-1 --api-group-id ag-xxx</code> | 返回分组详情 |
| 查询分组列表 | <code>jdc --output json ag describe-api-groups --region-id cn-north-1 --page-number 1 --page-size 50</code> | 支持分页 |
| 修改分组 | <code>jdc --output json ag modify-api-group --region-id cn-north-1 --api-group-id ag-xxx --group-name v2-service</code> | 更新分组属性 |
| 删除分组 | <code>jdc --output json ag delete-api-group --region-id cn-north-1 --api-group-id ag-xxx</code> | **级联删除**分组下所有 API；不可逆 |

### API 操作

| 目标 | `jdc` 调用示例 | 备注 |
|------|---------------|------|
| 创建 API | <code># 期望语法示例<br>jdc --output json ag create-api --region-id cn-north-1 --api-group-id ag-xxx --api-name get-user --request-config '{"requestPath":"/users/{userId}","requestMethod":"GET","requestProtocol":"HTTP"}' --service-config '{"serviceProtocol":"HTTP","serviceAddress":"http://user-svc.internal","servicePath":"/api/users/{userId}","serviceMethod":"GET"}' --auth-type app_auth</code> | `request-config` / `service-config` 为 JSON 字符串；`auth-type` ∈ `no_auth` / `app_auth` / `jdcloud_auth` |
| 查询单个 API | <code>jdc --output json ag describe-api --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx</code> | 返回 API 详情 |
| 查询 API 列表 | <code>jdc --output json ag describe-apis --region-id cn-north-1 --api-group-id ag-xxx --page-number 1 --page-size 50</code> | 按分组过滤 |
| 修改 API | <code>jdc --output json ag modify-api --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --api-name get-user-v2</code> | 更新 API 属性 |
| 删除 API | <code>jdc --output json ag delete-api --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx</code> | 从所有 stage 移除；不可逆 |

### 部署 / Stage 操作

| 目标 | `jdc` 调用示例 | 备注 |
|------|---------------|------|
| 部署 API | <code># 期望语法示例<br>jdc --output json ag deploy-api --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --stage-name prod --description "deployed via cli"</code> | `stage-name` ∈ `test` / `pre` / `prod` |
| 取消部署 | <code>jdc --output json ag undeploy-api --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --stage-name prod</code> | 从指定 stage 撤回 |
| 查询部署列表 | <code>jdc --output json ag describe-deployments --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx</code> | 返回各 stage 部署状态 |

### 流控策略操作

| 目标 | `jdc` 调用示例 | 备注 |
|------|---------------|------|
| 创建流控策略 | <code># 期望语法示例<br>jdc --output json ag create-throttling-policy --region-id cn-north-1 --policy-name tiered-limit --throttle-config '{"apiThrottleConfig":{"apiId":"api-xxx","unit":"minute","apiLimit":6000,"appLimit":600}}'</code> | `unit` ∈ `second` / `minute` / `hour` / `day` |
| 查询策略列表 | <code>jdc --output json ag describe-throttling-policies --region-id cn-north-1 --page-number 1 --page-size 50</code> | 列出全区域所有策略 |
| 绑定策略 | <code>jdc --output json ag bind-throttling-policy --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --stage-name prod --policy-id tpl-xxx</code> | 绑定到 API + stage |
| 解绑策略 | <code>jdc --output json ag unbind-throttling-policy --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --stage-name prod --policy-id tpl-xxx</code> | 解除绑定 |
| 查询 API 流控 | <code>jdc --output json ag describe-api-throttling --region-id cn-north-1 --api-group-id ag-xxx --api-id api-xxx --stage-name prod</code> | 查询 API 当前绑定的策略 |
| 删除策略 | <code>jdc --output json ag delete-throttling-policy --region-id cn-north-1 --policy-id tpl-xxx</code> | 须先解绑 |

## JSON Response Paths

### Create API Group
```json
{
  "requestId": "req-xxx",
  "result": {
    "apiGroupId": "ag-abc123"
  }
}
```
**Key paths:**
- `$.result.apiGroupId` — 新建 API 分组 ID

### Describe API Group
```json
{
  "requestId": "req-xxx",
  "result": {
    "apiGroup": {
      "apiGroupId": "ag-abc123",
      "groupName": "v1-service",
      "status": "Active",
      "description": "created via cli",
      "createTime": "2026-06-08T10:00:00+08:00"
    }
  }
}
```
**Key paths:**
- `$.result.apiGroup.apiGroupId` — 分组 ID
- `$.result.apiGroup.status` — 分组状态（`Active` / `Deleting`）
- `$.result.apiGroup.groupName` — 分组名

### Describe API Groups (List)
```json
{
  "requestId": "req-xxx",
  "result": {
    "apiGroups": [
      {
        "apiGroupId": "ag-abc123",
        "groupName": "v1-service",
        "status": "Active"
      }
    ],
    "totalCount": 1,
    "pageNumber": 1,
    "pageSize": 50
  }
}
```
**Key paths:**
- `$.result.apiGroups[*].apiGroupId` — 分组 ID 数组
- `$.result.totalCount` — 总数

### Create API
```json
{
  "requestId": "req-xxx",
  "result": {
    "apiId": "api-xyz789"
  }
}
```
**Key paths:**
- `$.result.apiId` — 新建 API ID

### Describe API
```json
{
  "requestId": "req-xxx",
  "result": {
    "api": {
      "apiId": "api-xyz789",
      "apiName": "get-user",
      "apiGroupId": "ag-abc123",
      "status": "UnDeployed",
      "authType": "app_auth",
      "requestConfig": {
        "requestPath": "/users/{userId}",
        "requestMethod": "GET",
        "requestProtocol": "HTTP"
      },
      "createTime": "2026-06-08T10:05:00+08:00"
    }
  }
}
```
**Key paths:**
- `$.result.api.apiId` — API ID
- `$.result.api.status` — API 状态（`UnDeployed` / `Deployed` / `Deleting`）
- `$.result.api.authType` — 鉴权类型
- `$.result.api.requestConfig.requestPath` — 请求路径

### Describe APIs (List)
```json
{
  "requestId": "req-xxx",
  "result": {
    "apis": [
      {
        "apiId": "api-xyz789",
        "apiName": "get-user",
        "status": "UnDeployed"
      }
    ],
    "totalCount": 1
  }
}
```
**Key paths:**
- `$.result.apis[*].apiId` — API ID 数组
- `$.result.apis[*].status` — 状态数组

### Deploy API
```json
{
  "requestId": "req-xxx",
  "result": {
    "deploymentId": "dep-abc456"
  }
}
```
**Key paths:**
- `$.result.deploymentId` — 部署 ID

### Describe Deployments
```json
{
  "requestId": "req-xxx",
  "result": {
    "deployments": [
      {
        "deploymentId": "dep-abc456",
        "stageName": "prod",
        "status": "Deployed",
        "deployTime": "2026-06-08T10:10:00+08:00"
      }
    ]
  }
}
```
**Key paths:**
- `$.result.deployments[*].stageName` — stage 名称
- `$.result.deployments[*].status` — 部署状态（`Deployed` / `Undeployed`）

### Create Throttling Policy
```json
{
  "requestId": "req-xxx",
  "result": {
    "policyId": "tpl-xyz789"
  }
}
```
**Key paths:**
- `$.result.policyId` — 策略 ID

### Describe API Throttling
```json
{
  "requestId": "req-xxx",
  "result": {
    "throttlings": [
      {
        "policyId": "tpl-xyz789",
        "policyName": "tiered-limit",
        "stageName": "prod",
        "apiLimit": 6000,
        "appLimit": 600,
        "unit": "minute"
      }
    ]
  }
}
```
**Key paths:**
- `$.result.throttlings[*].policyId` — 绑定的策略 ID
- `$.result.throttlings[*].apiLimit` — API 限流值
- `$.result.throttlings[*].stageName` — 生效 stage

## Common CLI Patterns

### Sandbox Setup（运行前初始化）

```bash
# 将 HOME 重定向到可写位置，创建 jdc 配置
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = apigateway.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

> 如 `jdc ag ...` 命令仍报 `invalid choice`，说明当前 jdc 版本尚未接入 API Gateway 产品——**立即回退到 Python SDK**（参见 `references/api-sdk-usage.md`）。

### Polling for Status（状态轮询）

```bash
# 轮询直到 API Group 变为 Active
for i in $(seq 1 15); do
  STATUS=$(jdc --output json ag describe-api-group \
    --region-id "cn-north-1" \
    --api-group-id "ag-abc123" \
    | jq -r '.result.apiGroup.status')
  echo "attempt=$i status=$STATUS"
  [ "$STATUS" = "Active" ] && break
  sleep 2
done

# 轮询直到 API 部署完成
for i in $(seq 1 12); do
  STATUS=$(jdc --output json ag describe-deployments \
    --region-id "cn-north-1" \
    --api-group-id "ag-abc123" \
    --api-id "api-xyz789" \
    | jq -r '.result.deployments[] | select(.stageName=="prod") | .status')
  echo "attempt=$i stage=prod status=$STATUS"
  [ "$STATUS" = "Deployed" ] && break
  sleep 5
done

# 轮询直到 API 消失（删除后验证）
for i in $(seq 1 15); do
  EXISTS=$(jdc --output json ag describe-api \
    --region-id "cn-north-1" \
    --api-group-id "ag-abc123" \
    --api-id "api-xyz789" 2>/dev/null | jq -r '.result.api.apiId // "gone"')
  echo "attempt=$i exists=$EXISTS"
  [ "$EXISTS" = "gone" ] && break
  sleep 2
done
```

### Extracting Values with `jq`（常用提取模式）

```bash
# 从创建响应中提取 API Group ID
AG_ID=$(jdc --output json ag create-api-group \
  --region-id cn-north-1 \
  --group-name v1-service \
  | jq -r '.result.apiGroupId')

# 从创建响应中提取 API ID
API_ID=$(jdc --output json ag create-api ... \
  | jq -r '.result.apiId')

# 列出所有 API Group ID
AG_IDS=$(jdc --output json ag describe-api-groups \
  --region-id cn-north-1 \
  | jq -r '.result.apiGroups[].apiGroupId')

# 列出指定 Group 下所有 Deployed API
DEPLOYED=$(jdc --output json ag describe-apis \
  --region-id cn-north-1 \
  --api-group-id ag-abc123 \
  | jq -r '.result.apis[] | select(.status=="Deployed") | .apiId')

# 提取部署 ID
DEP_ID=$(jdc --output json ag deploy-api \
  --region-id cn-north-1 \
  --api-group-id ag-abc123 \
  --api-id api-xyz789 \
  --stage-name prod \
  | jq -r '.result.deploymentId')

# 提取流控策略 ID
POLICY_ID=$(jdc --output json ag create-throttling-policy ... \
  | jq -r '.result.policyId')
```

### Pagination（分页遍历）

```bash
fetch_all_groups() {
  local region="$1"
  local page=1
  local all="[]"
  while : ; do
    local resp
    resp=$(jdc --output json ag describe-api-groups \
      --region-id "$region" \
      --page-number "$page" \
      --page-size 100)
    local batch total
    batch=$(echo "$resp" | jq '.result.apiGroups // []')
    total=$(echo "$resp" | jq '.result.totalCount // 0')
    all=$(jq -s 'add' <(echo "$all") <(echo "$batch"))
    local batch_count
    batch_count=$(echo "$batch" | jq 'length')
    [ "$batch_count" -lt 100 ] && break
    page=$((page + 1))
    [ "$page" -gt 50 ] && { echo "WARN: pagination>50" >&2; break; }
    [ "$total" -gt 0 ] && [ "$(jq 'length' <<< "$all")" -ge "$total" ] && break
  done
  echo "$all"
}
```

### 重试与错误兜底

```bash
run_with_retry() {
  local max=3 delay=0 attempt=0
  while [ $attempt -lt $max ]; do
    if "$@"; then return 0; fi
    attempt=$((attempt + 1))
    delay=$((delay == 0 ? 2 : delay * 2))
    echo "RETRY attempt=$attempt delay=${delay}s" >&2
    sleep "$delay"
  done
  return 1
}

# 示例：创建 API Group 带重试
run_with_retry jdc --output json ag create-api-group \
  --region-id cn-north-1 \
  --group-name v1-service
```

### 常见 jdc CLI 错误到回退策略

| 错误现象 | 原因 | 回退 |
|---------|------|------|
| `invalid choice: 'ag'` / `'apigateway'` | jdc 版本未接入 API Gateway | 立即切到 Python SDK（`api-sdk-usage.md`） |
| `InvalidParameter` | 参数格式错（尤其 JSON 字符串） | 用 `jq .` 先校验 JSON 再传参 |
| `Unauthorized` | `~/.jdc/config` 凭证错误 | 检查 access_key / secret_key |
| `QuotaExceeded` | 配额已满 | HALT，提示用户申请配额 |
| `RateLimitExceeded` | CLI 内部流控 | 指数退避重试 |
| `ResourceNotFound` | ID 错误或已删除 | 先 `describe-*` 确认存在 |

## Output Format

`--output` 顶层参数指定输出格式：

| 格式 | 用途 |
|------|------|
| `json` | 自动化（本 skill **唯一推荐**） |
| `table` | 人眼查看（调试用） |
| `text` | 纯文本（极少用） |

```bash
jdc --output table ag describe-api-groups --region-id cn-north-1
```

## Global Arguments

| 参数 | 说明 |
|------|------|
| `--debug` | 显示调试信息 |
| `--output` | 输出格式（json/table/text），**必须放在子命令之前** |
| `--profile` | 使用指定 INI profile |
| `--region-id` | 区域 ID（API Gateway 支持 `cn-north-1` 等） |

## 跨 Skill 命令速查

| 任务 | CLI 命令 | 委派给 |
|------|---------|--------|
| 创建 API Group | `jdc ag create-api-group` | **本 skill** |
| 创建 API | `jdc ag create-api` | **本 skill** |
| 部署 / 回滚部署 | `jdc ag deploy-api` / `undeploy-api` | **本 skill** |
| 绑定流控策略 | `jdc ag bind-throttling-policy` | **本 skill** |
| 查询 API 调用日志 / 指标 | 可能在 `jdc logservice` / `jdc monitor` | `jdcloud-logservice-ops` / `jdcloud-cloudmonitor-ops` |
| 自定义域名绑定 | 可能在 `jdc ag bind-domain`（未验证） | **本 skill** 或 `jdcloud-dns-ops` |

## 参考链接

- [API & SDK Usage](./api-sdk-usage.md)
- [Core Concepts](./core-concepts.md)
- [SKILL.md](../SKILL.md)（含 SDK-only 定位、变量约定、状态机）
- [JD Cloud CLI 官方仓库](https://github.com/jdcloud-api/jdcloud-cli)
- [API