# JD Cloud Skills Farm

## Quick Identity

**JD Cloud Skills Farm** is a collection of AI Agent Skill definitions (structured Markdown documents following the Agent Skill OpenSpec) that enable AI agents to perform JD Cloud (京东云) operations. Each skill maps to one JD Cloud product.

## Repo Layout

```
jdcloud-skills/
├── README.md / README_EN.md       # Bilingual project docs
├── QUICK_START.md / QUICK_START_EN.md  # Bilingual quick start
├── jdcloud-skill-generator/       # Meta Skill — generates new product skills
├── jdcloud-vm-ops/                # VM lifecycle + cloud assistant
├── jdcloud-redis-ops/             # Redis cache management
├── jdcloud-oss-ops/               # OSS — object storage
├── jdcloud-nat-ops/               # NAT — NAT gateway
├── jdcloud-kubernetes-ops/        # K8s — Kubernetes cluster management
├── jdcloud-cloudmonitor-ops/      # Cloud Monitor — metrics, alarms
├── jdcloud-iam-ops/               # IAM — users, groups, roles, policies
├── jdcloud-kms-ops/               # KMS — key management, encryption
├── jdcloud-clb-ops/               # CLB — load balancer management
├── jdcloud-disk-ops/              # Cloud Disk — data disks, snapshots
├── jdcloud-fc-ops/                # Function Compute — serverless functions
├── jdcloud-waf-ops/               # WAF — Web Application Firewall
├── jdcloud-alert-intelligence/    # Alert post-processing (aggregation, suppression, reporting)
├── jdcloud-billing-ops/          # Billing — balance, consumption, vouchers, cost estimation
├── jdcloud-routines-ops/         # Routine ops — expiry cruise, resource inventory
├── jdcloud-dns-ops/               # DNS — domain/record management
├── jdcloud-cert-ops/              # SSL Certificate — certificate lifecycle
├── .env.example / pyproject.toml / uv.lock
└── AGENTS.md                      # ← this file
```

## Every Skill Directory Follows

```
jdcloud-[product]-ops/
├── SKILL.md                    # Main skill definition (entry point)
├── assets/example-config.yaml  # Sample configs
└── references/
    ├── cli-usage.md
    ├── core-concepts.md
    ├── api-sdk-usage.md
    ├── integration.md
    ├── monitoring.md
    ├── troubleshooting.md
    ├── rubric.md
    └── prompt-templates.md
    ├── rubric.md
    └── prompt-templates.md
```

## AIOps Cruise Skill Directory Structure (Three-Phase Model)

**AIOps 巡检类 Skill**（如 `jdcloud-aiops-cruise`）遵循 **Perceive → Reason → Execute** 三阶段模型，目录结构必须体现这三个分类：

```
jdcloud-aiops-cruise/
├── SKILL.md                    # Skill 定义（入口）
├── runbooks/                   # 巡检场景定义
│   ├── 00-index.md             #   场景索引
│   ├── 01-daily-health-check.md
│   ├── 02-emergency-troubleshoot.md
│   ├── 03-capacity-planning.md
│   ├── 04-pre-launch-check.md
│   └── 05-mysql-slowquery-audit.md
├── scripts/                    # 执行脚本（三阶段分层）
│   ├── 01-perceive/            #   感知层 — 数据收集与拓扑发现
│   │   └── cruise_sniff.py     #     Phase 1: 资源嗅探 + 拓扑初判
│   ├── 02-reason/              #   推理层 — 分析与诊断
│   │   ├── cruise_link.py      #     Phase 2: 全链路深度巡检编排器
│   │   └── analyzers/          #     各资源类型分析器
│   │       ├── base_analyzer.py
│   │       ├── vm_analyzer.py
│   │       ├── clb_analyzer.py
│   │       ├── eip_analyzer.py
│   │       ├── redis_analyzer.py
│   │       ├── rds_mysql_analyzer.py
│   │       ├── k8s_analyzer.py
│   │       ├── nat_analyzer.py
│   │       ├── es_analyzer.py
│   │       └── sg_analyzer.py
│   ├── 03-execute/             #   执行层 — 修复建议与闭环
│   │   └── README.md           #     说明：本层只生成建议，不直接执行变更
│   ├── lib/                    #   共享库
│   │   ├── jdc_client.py       #     JD Cloud CLI/SDK 封装
│   │   └── resource_discovery.py
│   └── README.md               #   脚本结构说明
├── references/                 # 参考文档
│   ├── prompt-templates.md     #   GCL Prompt 模板
│   ├── severity-matrix.md      #   严重级别矩阵
│   └── threshold-definitions.md #   阈值定义
└── reports/                    # 报告输出
    └── templates/              #   报告模板
```

### 三阶段职责划分

| 阶段 | 目录 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| **Perceive** | `01-perceive/` | 数据采集、资源发现、拓扑构建 | 客户标签、区域范围 | 拓扑初判报告 |
| **Reason** | `02-reason/` | 指标分析、异常检测、根因定位 | Phase 1 输出、监控数据 | 深度巡检报告 |
| **Execute** | `03-execute/` | 修复建议生成、闭环跟踪 | Phase 2 findings | Action 建议（供人工确认） |

### 关键设计约束

1. **Execute 层只读原则**: `jdcloud-aiops-cruise` 是纯只读巡检 Skill，`03-execute/` 不放置实际变更脚本，只生成标准化的修复建议，供人工确认后通过对应 ops skill 执行。

2. **路径约定**: 脚本导入路径必须兼容三阶段目录结构：
   ```python
   # 在 01-perceive/ 或 02-reason/ 子目录中的脚本
   _scripts_dir = os.path.dirname(os.path.abspath(__file__))
   _project_dir = os.path.join(_scripts_dir, "..")  # 指向 scripts/
   sys.path.insert(0, _project_dir)
   from lib.jdc_client import JdcClient
   ```

3. **命名规范**:
   - `01-perceive/*_sniff.py` — 嗅探/发现类脚本
   - `02-reason/*_link.py` — 分析/关联类脚本
   - `02-reason/analyzers/*_analyzer.py` — 特定资源分析器
   - `03-execute/*_action.py` — 建议生成器（如有）

### 执行顺序

```bash
# Phase 1: 感知
python scripts/01-perceive/cruise_sniff.py --customer 烟台振华

# Phase 2: 推理
python scripts/02-reason/cruise_link.py --customer 烟台振华 --sniff-file reports/output/sniff-xxx.json

# Phase 3: 执行建议（人工确认后调用对应 skill）
# 根据 Phase 2 报告，由人工通过 jdcloud-vm-ops / jdcloud-redis-ops 等执行实际变更
```

### 为什么需要三阶段分离

1. **职责清晰**: 每个阶段有明确的输入输出契约，便于独立测试和迭代
2. **安全隔离**: Execute 层可独立审计，确保变更操作可控
3. **扩展友好**: 新增资源类型只需在 `02-reason/analyzers/` 添加 analyzer
4. **符合 AIOps 认知模型**: Perceive/Reason/Execute 是行业通用框架

## Development Environment

**Python 3.10** | **`uv`** (package manager) | **`jdc`** (JD Cloud CLI)

> **IMPORTANT: Python version must be 3.10, NOT 3.12.**
> `jdcloud_cli==1.2.12` imports `SafeConfigParser` from `configparser`, which was **removed in Python 3.12**. Using Python 3.12+ will cause an `ImportError` and make the CLI unusable.
>
> Always use `uv venv --python 3.10` to create the virtual environment. If Python 3.10 is not installed on your system, install it first:
> - macOS: `brew install python@3.10`
> - Linux: `apt install python3.10 python3.10-dev` or `uv python install 3.10`
> - Windows: Download from https://www.python.org/downloads/release/python-3100/

### Setup

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

`pyproject.toml` pins `jdcloud_cli==1.2.12`. The default pip index is `https://mirrors.aliyun.com/pypi/simple/` (configured under `[tool.uv]`).

### MANDATORY Pre-flight Checks (Agent MUST Execute Before ANY jdc Command)

**CRITICAL: Agent MUST verify the following BEFORE attempting to use `jdc` CLI. Failure to do so will result in `command not found` errors.**

| Check | Command | Expected Result | On Failure |
|-------|---------|-----------------|------------|
| **1. Python version** | `python --version` | `Python 3.10.x` (NOT 3.12+) | HALT; recreate venv with `uv venv --python 3.10` |
| **2. Virtual env exists** | `test -d .venv && echo "OK"` | `OK` | Run `uv venv --python 3.10` |
| **3. Virtual env activated** | `echo $VIRTUAL_ENV` | Absolute path ending in `/.venv` | Run `source .venv/bin/activate` |
| **4. jdc binary location** | `which jdc` | `.venv/bin/jdc` (MUST be in .venv) | Reinstall: `uv pip install --no-cache jdcloud_cli==1.2.12` |
| **5. jdc executable** | `jdc --version` | `1.2.12` | Reinstall: `uv pip install --no-cache jdcloud_cli==1.2.12 jdcloud_sdk` |
| **6. Credentials configured** | `test -n "$JDC_ACCESS_KEY" && test -n "$JDC_SECRET_KEY"` | Exit code 0 | Load from `.env` or prompt user |
| **7. jdc config file** | `test -f ~/.jdc/config && test -f ~/.jdc/current` | Both files exist | Create config (see Credentials section below) |

**Agent Execution Protocol (MANDATORY):**

```bash
# Step 1: Activate virtual environment (ALWAYS first)
source .venv/bin/activate

# Step 2: Verify Python version
python --version  # MUST be 3.10.x

# Step 3: Verify jdc is in .venv
which jdc  # MUST output: /path/to/project/.venv/bin/jdc

# Step 4: Verify jdc works
jdc --version  # MUST output: 1.2.12

# Step 5: Load credentials (if not in shell env)
if [ -f .env ]; then
  export $(grep -E '^JDC_' .env | xargs)
fi

# Step 6: Configure jdc CLI (sandbox-safe)
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = nc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Step 7: Test jdc command
jdc --output json nc describe-clusters --region-id cn-north-1 --page-number 1 --page-size 1
```

**Common Mistakes (BANNED):**

| ❌ Wrong | ✅ Correct | Why |
|---------|-----------|-----|
| `jdc vm list` (without activating venv) | `source .venv/bin/activate && jdc --output json vm list` | `jdc` binary is in `.venv/bin/`, not in system PATH |
| Assuming `jdcloud_cli` is installed | `which jdc && jdc --version` | Package may be installed in wrong Python environment |
| `pip install jdcloud_cli` (system pip) | `uv pip install jdcloud_cli` (after `source .venv/bin/activate`) | System pip installs to system Python, not .venv |
| Using Python 3.12 | `uv venv --python 3.10` | `jdcloud_cli==1.2.12` uses `SafeConfigParser` removed in Python 3.12 |
| Setting only env vars for CLI | Writing `~/.jdc/config` INI file | jdc CLI reads ONLY from config file, NOT from env vars |

**Agent Self-Check Question (Before ANY jdc Execution):**

> "Did I just run `source .venv/bin/activate` and verify `which jdc` points to `.venv/bin/jdc`?"
>
> If NO → **STOP** and run the Pre-flight Checks above.
> If YES → Proceed with jdc command.

### Credentials

Three methods (priority order: shell env > `.env` > `~/.jdc/config`):

```bash
# Method 1: .env file (recommended for local dev)
cp .env.example .env
# Edit with real credentials; .env is in .gitignore

# Method 2: CLI config for jdc
jdc config init              # interactive
# Or manual:
export HOME=/tmp/jdc-home    # sandbox-safe writable home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
endpoint = vm.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

**CRITICAL: jdc CLI reads credentials ONLY from `~/.jdc/config` INI file, NOT from environment variables.** The SDK reads from `JDC_ACCESS_KEY`/`JDC_SECRET_KEY` env vars. Both must be configured.

**NEVER** print or log `JDC_SECRET_KEY`. Only check existence with `test -n`.

## jdc CLI Quirks (Hard-Earned)

These are the most common agent mistakes — get them right every time:

| Rule | Wrong | Correct |
|------|-------|---------|
| `--output json` placement | `jdc vm list --output json` | `jdc --output json vm list` |
| `--no-interactive` flag | `jdc --no-interactive vm delete` | **Omit entirely** — not supported |
| Credentials | `export JDC_ACCESS_KEY=...` (CLI ignores) | Must write `~/.jdc/config` INI file |
| `~/.jdc/current` newline | `echo "default" > file` (adds newline) | `printf "%s" "default" > file` (no trailing newline) |

## Execution Strategy

**jdc-first with SDK fallback** — the repository-wide policy:

1. Try `jdc --output json <command>` first
2. On failure, retry up to 3 times with exponential backoff (0s → 2s → 4s)
3. After 3 consecutive failures, fall back to Python SDK (`jdcloud_sdk`)
4. Document which path was used

## Skill SKILL.md Anatomy

Every `SKILL.md` uses:
- **YAML frontmatter** with `name`, `version`, `metadata` (including `cli_applicability`, `cli_version_locked`, `sdk_version_locked`)
- **Trigger & Scope** — `SHOULD Use` / `SHOULD NOT Use` with delegation rules
- **Variable Convention** — `{{env.*}}` (runtime, never prompt user), `{{user.*}}` (ask once, cache), `{{output.*}}` (parse from JSON response)
- **Execution Flows** — Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover
- **Output Parsing Rules** — JSON paths (`$.result.*`) and state transition tables
- **Failure Recovery** — Error pattern tables with retry counts, backoff, and agent actions
- **Safety Gates** — Delete/recovery operations REQUIRE explicit user confirmation

## Cross-Skill Delegation

When a user's request spans multiple JD Cloud products:

| If they ask about | Delegate to |
|---|---|
| Full-link inspection / topology discovery / root-cause across services | `jdcloud-aiops-cruise` |
| VM create/stop/delete | `jdcloud-vm-ops` |
| Redis instance CRUD | `jdcloud-redis-ops` |
| MySQL instance CRUD, slow query, backup/restore | `jdcloud-mysql-ops` |
| PostgreSQL instance CRUD, slow query, backup/restore | `jdcloud-postgresql-ops` |
| MongoDB instance CRUD | `jdcloud-mongodb-ops` |
| Elasticsearch cluster/index CRUD | `jdcloud-elasticsearch-ops` |
| VPC/Subnet/Security Group/Route Table/ACL management | `jdcloud-vpc-ops` |
| Architecture review / WAF assessment / Recommendation | `jdcloud-arch-advisor` |
| Monitoring metrics, alarm rules | `jdcloud-cloudmonitor-ops` |
| Alert analysis, suppression, reporting | `jdcloud-alert-intelligence` |
| IAM users, policies, keys | `jdcloud-iam-ops` |
| Key management, encryption | `jdcloud-kms-ops` |
| EIP allocate/associate/release | `jdcloud-eip-ops` |
| Load balancer config | `jdcloud-clb-ops` |
| OSS bucket/object CRUD, storage management | `jdcloud-oss-ops` |
| NAT gateway/SNAT/DNAT rules | `jdcloud-nat-ops` |
| Kubernetes cluster/node group mgmt | `jdcloud-kubernetes-ops` |
| Cloud Disk CRUD, attach/detach, snapshot | `jdcloud-disk-ops` |
| Function Compute service/function/trigger | `jdcloud-fc-ops` |
| Web Application Firewall instance/domain/rule | `jdcloud-waf-ops` |
| API Gateway instance/API/consumer | `jdcloud-apigateway-ops` |
| Tag audit / untagged resource detection / DOPS ticket | `jdcloud-tag-audit-ops` |
| Audit event query / trail lookup | `jdcloud-audit-ops` |
| VPN tunnel/routing config | `jdcloud-vpn-ops` |
| Topology graph rendering (visual layer over aiops-cruise output) | `jdcloud-topo-discovery` |
| Log service / LogQL / index config | `jdcloud-logservice-ops` |
| Message queue / topic / consumer group | `jdcloud-jcq-ops` |
| DNS domain/record CRUD, DNS monitoring, custom lines | `jdcloud-dns-ops` |
| SSL certificate upload/query/download/delete, cert expiry cruise | `jdcloud-cert-ops` |
| Generate a new product skill | `jdcloud-skill-generator` |
| Routine operations (expiry cruise, resource inventory) | `jdcloud-routines-ops` |
| **Billing / cost / account balance / voucher / invoice** | **`jdcloud-billing-ops`** |

**Cross-skill routing rules (read-only delegation chains):**

- `jdcloud-aiops-cruise` is **read-only** — it produces findings and recommends changes but delegates ALL mutations to product-specific ops skills (vm/redis/mysql/postgresql/clb/eip/nat/k8s/waf/etc.).
- `jdcloud-alert-intelligence` is **read-only** — it analyzes alerts but delegates alarm rule changes back to `jdcloud-cloudmonitor-ops` and delegates product fixes to product-specific ops skills.
- `jdcloud-routines-ops` is **read-only** for its core flows (expiry cruise / inventory); any renewal or modification is delegated to product ops skills.
- `jdcloud-billing-ops` is **read-only** for billing queries; it delegates any account modifications (recharge) to the JD Cloud console.
- `jdcloud-tag-audit-ops` is **read-only** for tag inspection; tag changes are delegated to product ops skills.
- `jdcloud-audit-ops` is **read-only** — it queries audit events but does not modify them.
- Each skill's `SHOULD NOT Use` section lists exactly where to route.

## Validation

### Markdown（Skill 文档）

```bash
npm install -g markdownlint-cli
markdownlint jdcloud-[product]-ops/SKILL.md
```

### Python（脚本 / Skill 代码）

所有 Python 变更（新增、修改、重构）完成后 **必须** 通过 Ruff 检查并自动格式化。
Ruff 同时承担 lint + format 职责（替代 flake8 / isort / black / pyupgrade）。

**安装**（一次性；项目 `pyproject.toml` 已声明 `ruff>=0.6` 为 dev 依赖）：

```bash
source .venv/bin/activate
uv pip install "ruff>=0.6"
```

**变更完成后必跑**（Agent 自我验收三步，缺一不可）：

```bash
# 1) lint：检查语法、未使用导入、可简化分支、bug 风险等
ruff check .

# 2) format：自动按仓库统一风格（双引号、空格缩进、line-length=100）格式化
ruff format .

# 3) 复核：lint 必须再次零错误
ruff check .
```

**强制要求**：

| 场景 | 要求 |
|---|---|
| 新增 / 修改任何 `.py` 文件 | `ruff check .` + `ruff format .` 必须全部通过，**禁止带着 lint 错误提交** |
| `ruff check .` 报 `# noqa` 之外的非空结果 | **视为未完成**，先修代码或调整规则（不要 `noqa` 堆叠） |
| 仓库 `pyproject.toml` 的 `[tool.ruff]` 已锁定规则集 | 改动规则需在 PR 描述里说明原因；不要在本地静默改规则绕过报错 |
| `clean_python.sh` 顺带清理 `.ruff_cache` | 提交前可运行 `./clean_python.sh --yes` 一并清掉缓存 |

**CI 落地建议**（`.github/workflows/ruff.yml`，本仓库未启用时按下例追加）：

```yaml
name: ruff
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v1
        with:
          args: "check --output-format=github ."
      - run: ruff format --check .
```

**不在范围**（明确不做，避免过度工程）：

- 不强制 mypy / pyright 类型检查 — 仓库脚本以调用 SDK 为主，类型收益低、迁移成本高。
- 不强制 `ruff format` 与 `black` 100% 等价的全部细节；以 Ruff format 为准。
- 不引入 pre-commit 框架 — Agent 手动跑三步即可落地，避免额外依赖。

## Versioning

SemVer in `SKILL.md` frontmatter. Update `version` field + Changelog table when modifying. The `version` field reflects the skill document version, not the SDK version (tracked separately in `metadata.sdk_version_locked`).

## Security Rules

- `{{env.*}}` placeholders are resolved from agent runtime — **never prompt the user**
- `.env` is gitignored; never commit real credentials
- Delete/stop/restore operations require explicit user confirmation ("safety gate")
- `jdcloud-alert-intelligence` is read-only — no resource mutations
- Credential status checks: `test -n "$VAR"` only, print `<masked>` if logging status

## Self-Review Policy

Every skill update MUST follow a **2-round self-review process** to ensure quality and correctness:

### Round 1: Initial Review
After creating or modifying a skill:
1. Review the skill against the template and existing reference skills
2. Verify all required sections are present (frontmatter, Trigger & Scope, Variable Convention, Execution Flows, etc.)
3. Check for consistency with jdc-first with SDK fallback strategy
4. Validate safety gates are in place for destructive operations

### Round 2: Deep Review
After Round 1 fixes are applied:
1. Verify API accuracy against official OpenAPI specifications
2. Validate CLI command syntax and JSON output paths
3. Check cross-skill delegation rules are correctly defined
4. Confirm versioning follows SemVer and changelog is updated

### Auto-Fix Requirement
All issues discovered during both review rounds MUST be proactively fixed before the skill is considered complete. This includes:
- Correcting API parameters and response paths
- Fixing CLI command syntax
- Adding missing safety gates
- Updating documentation inconsistencies
- Ensuring alignment with repository-wide conventions

### Post-Change Self-Review (Mandatory)
**After EVERY code or documentation change, the Agent MUST perform a structured self-review BEFORE claiming completion.**

**Trigger**: Any edit to `.py`, `.md`, `.yaml`, `.json` files in the repository.

**Review Checklist**:
| # | Check | Action if Failed |
|---|-------|------------------|
| 1 | **ruff check** passes | Run `ruff check --fix` and fix remaining manually |
| 2 | **ruff format** applied | Run `ruff format .` |
| 3 | **Tests pass** | Run `pytest` for affected modules; fix or update tests |
| 4 | **No F821/F822** (undefined names) | Fix immediately — runtime risk |
| 5 | **Commit size reasonable** | If >20 files, consider splitting commits |
| 6 | **BACKLOG.md sync** | If skill status changed, update BACKLOG |
| 7 | **Self-critique** | Ask: "What could break? What did I miss?" |

**Self-Review Output Format**:
```markdown
## Self-Review: <change-summary>

### ✅ Passed
- ruff check: X errors (all fixable / fixed)
- Tests: Y/Z passed
- ...

### ⚠️ Issues Found
- <issue-1>: <fix-applied>
- <issue-2>: <fix-applied>

### 🎯 Score
<0-10>/10 — <reason>

### 🔧 Action Items
- [ ] <if-any-deferred>
```

**Enforcement**: This is a required step. The Agent MUST NOT claim "done" or create PR without completing this checklist.

---

## Generator-Critic-Loop (GCL) — Adversarial Quality Gate

> Inspired by GAN's Generator/Discriminator idea, but deliberately **not** a real GAN.
> Naming: **GCL (Generator-Critic-Loop)** to avoid misleading reviewers and LLM trainees.

### 1. Purpose

Apply an adversarial **Generator ↔ Critic** loop with a quantitative rubric to every skill execution.
Most valuable in **high-side-effect cloud operations** (delete, stop, restore, IAM/KMS/DDL) where a single
mistake is unrecoverable.

| GAN (real) | GCL (this spec) |
|---|---|
| Discriminator learns sample distribution | Critic scores an **explicit rubric** |
| No termination condition | Must terminate: **PASS / MAX_ITER / SAFETY_FAIL** |
| G and D train in parallel | G and C run **sequentially** |
| Goal: "fool the D" | Goal: "pass the rubric threshold" |

### 2. Roles

| Role | Job | Input | Output | Forbidden |
|---|---|---|---|---|
| **Generator (G)** | Execute the cloud operation | user request + previous Critic feedback | result + execution trace | modifying the rubric; self-scoring |
| **Hallucination Detector (H)** | Pre-execution structural validity check | G's generated command / JSON + skill's reference knowledge base | pass/fail signal + hallucination report | executing API calls (read-only offline check only); modifying G's output |
| **Critic (C)** | Independently audit G's output | G's result + trace + rubric | scores + suggestions | calling jdc / SDK / mutating anything |
| **Orchestrator (O)** | Loop control, termination, final return | context + C scores + H result + budget | continue / final result | executing or scoring on its own |

**Hard constraint:** G and C MUST live in **isolated prompt contexts** (preferably isolated sessions
or sub-agents). A shared context is a "pseudo-GCL" and is explicitly banned — see §9.
H is a **deterministic offline check** by default (the Phase 6 mechanical H); it does NOT need isolation
because it never calls cloud APIs. A future LLM-based H would require the same isolation as C.

### 2.1 Critic Test & Regression Assessment (MANDATORY)

> **Core principle — accuracy over coverage**: Do **not** optimize for coverage metrics or test count. Optimize for whether tests **accurately** validate changed behavior and would **reliably catch** real regressions.

On **every** critique iteration, C MUST evaluate two acceptance dimensions **in addition to** the rubric:

| Assessment | C action | On failure |
|------------|----------|------------|
| **Test accuracy** | Judge whether existing tests **correctly** exercise and assert behaviors touched by this change. Ask: *if this change introduced a bug, would these tests fail?* Reject stale tests, wrong contracts, masked failures, or cases that touch code without validating outcomes | `blocking=true`; concrete test fixes/additions in `suggestions`; **RETRY** — no PASS until accurate for the change |
| **Regression verification gate** | Decide whether targeted regression ([AGENTS.md §11.1](#111-regression-testing-mandatory)) is required — pick the **smallest accurate suite** for the change and adjacent risk, not blanket runs for coverage theater | If required: name suite(s) and why sufficient; require green runs in trace/summary. If waived: document zero-behavioral-delta rationale |

**Decision posture**: Professional and cautious — when ambiguous, require targeted regression with tests that would actually fail on breakage.

| Change signal | C default |
|---------------|-----------|
| Pure docs/formatting (confirmed zero behavior delta) | Runtime regression optional; document skip rationale |
| Scripts / SkillOpt / execution flow / shared runtime | Run §11.1 suite(s) **only where they accurately exercise the changed path**; fix shallow assertions |
| Cross-skill or generator / `gen-skillopt.sh` | Shared integration + ≥1 representative test that **traverses the changed contract** |
| Refactor or intentional behavior change | Test-first: lock accurate before/after behavior, then applicable suites |

**Banned**: padding test count, chasing coverage %, PASSing on green suites that do not assert the changed behavior.

O treats inaccurate tests or missing required regression evidence like any other blocking C finding.

### 3. Rubric (mandatory per skill)

Each `SKILL.md` MUST declare its skill-specific rubric. Minimum 5 dimensions:

| Dimension | Meaning | Scale | Default threshold |
|---|---|---|---|
| **Correctness** | Resource id / state / config actually matches the request | 0 / 0.5 / 1 | ≥ 0.5 (1.0 required for `delete` / `stop` / IAM / KMS / DDL) |
| **Safety** | Destructive op (`delete` / `stop` / `restore` / IAM / KMS / DDL) was confirmed or guarded | 0 / 1 | = 1 |
| **Idempotency** | Retrying the same call will not cause duplicate side-effects | 0 / 0.5 / 1 | ≥ 0.5 |
| **Traceability** | Output is auditable: command, params, raw response, errors all captured | 0 / 0.5 / 1 | ≥ 0.5 |
| **Spec Compliance** | Conforms to the skill's `core-concepts.md` constraints | 0 / 0.5 / 1 | ≥ 0.5 |

**Safety = 0 → ABORT immediately, regardless of total score.**

### 4. Loop Flow

```
User Request
     │
     ▼
[0] Pre-flight (Orchestrator)
    - resolve env.* and user.* variables
    - pick skill, load its rubric
    - [Optional] 检索 failure-patterns.md 中与当前 skill 相关的已知模式
      → 将已知模式注入 Generator 上下文（预防性提示，非强制约束）
     │
     ▼
[1] Generate (G)
    - generate command / JSON payload (DO NOT execute yet) ──┐
    - pass command + skill context to H                      │
     │                                                       │
     ▼                                                       │
[1.5] Hallucination Detection (H)                           │
    - check API parameter existence                          │
    - check JSON structure against OpenAPI schema            │
    - check time range validity (≤ 90 days for audit)        │
     │                                                       │
     ├── PASS → [1a] Execute (run the command)               │
     ├── FAIL → [1b] Regenerate (H retriggers G with         │
     │               hallucination report; max 1 retry)      │
     │         still FAIL → HALT with "HALLUCINATION_ABORT"  │
     │                                                       │
     ▼                                                       │
[2] Critique (C)                                            │
    - isolated prompt context                                │
    - score every rubric dimension                           │
    - assess test accuracy + regression gate (§2.1)          │
    - emit ≤ 3 actionable suggestions                        │
     │                                                       │
     ▼                                                       │
[3] Decide (Orchestrator)                                   │
    - HALLUCINATION_ABORT → ABORT (no partial)               │
    - Safety=0  → ABORT (no partial)                         │
    - all pass  → RETURN                                     │
    - else & iter<max → inject                               │
       suggestions into G                                    │
    - else → RETURN best + unresolved                        │
       rubric items                                          │
     └───────────────────────────────────────────────────────┘
```

### 5. Termination (first match wins)

| Condition | Behavior |
|---|---|
| **PASS** | Every rubric dimension meets its threshold → return G's result |
| **MAX_ITER** | Reached `max_iterations` (default per skill class — see §8) → return **best-so-far** + unresolved rubric items |
| **SAFETY_FAIL** | Safety = 0 → **ABORT**; never return partial or "best-effort" output |
| **HALLUCINATION_ABORT** | H layer structural validity check fails after regeneration → **ABORT**; return unresolved hallucination report |

`max_iterations` defaults per skill class — see §8.

### 6. Trace & Audit (mandatory)

Every GCL run MUST persist a JSON trace:

```json
{
  "skill": "jdcloud-vm-ops",
  "request": "<sanitized user request>",
  "rubric_version": "v1",
  "iterations": [
    {
      "iter": 1,
      "generator": { "command": "...", "args": {...}, "exit_code": 0, "result_excerpt": "..." },
      "critic": {
        "scores": {
          "correctness": 1, "safety": 1, "idempotency": 0.5,
          "traceability": 1, "spec_compliance": 1
        },
        "suggestions": ["..."],
        "blocking": false
      },
      "decision": "RETRY"
    }
  ],
  "final": { "status": "PASS", "iter": 2, "output": "..." }
}
```

Path: `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` — unified with the existing
`audit-results/` directory used by `jdcloud-audit-ops` and `jdcloud-tag-audit-ops`.

### 7. Prompt Templates (mandatory per skill)

Each skill's `references/prompt-templates.md` MUST contain:

1. **Generator Prompt Template** — placeholders: `{{user.request}}`, `{{output.critic_feedback}}`, `{{output.rubric}}`
2. **Critic Prompt Template** — placeholders: `{{output.generator_output}}`, `{{output.trace}}`, `{{output.rubric}}`

> **Placeholder syntax** MUST follow the repository-wide convention
> (see top-level **Variable Convention**): `{{env.*}}` / `{{user.*}}` / `{{output.*}}`.
> Bare `{...}` placeholders are NOT allowed in skill prompt templates.

**Critic prompt must hide the raw user request** to prevent "answer-aligned" rubber-stamping.
Recommended skeleton:

```text
You are an independent cloud-operation auditor.
You will see one execution result and its trace. Score it STRICTLY against the rubric below.
Do NOT consider the original user request — judge only what was actually done.

rubric: {{output.rubric}}
generator_output: {{output.generator_output}}
trace: {{output.trace}}

Return strict JSON:
{
  "scores": { "correctness": 0|0.5|1, "safety": 0|0.5|1, "idempotency": 0|0.5|1,
              "traceability": 0|0.5|1, "spec_compliance": 0|0.5|1 },
  "suggestions": ["≤ 3 concrete, executable improvements"],
  "blocking": true|false
}
```

### 8. Per-Skill Defaults

| Skill | GCL | Default max_iter | Notes |
|---|---|---|---|
| `jdcloud-vm-ops` | **required** | 2 | delete/stop are destructive |
| `jdcloud-redis-ops` | **required** | 2 | flushall / instance delete |
| `jdcloud-mysql-ops` | **required** | 2 | DROP / DELETE / TRUNCATE |
| `jdcloud-postgresql-ops` | **required** | 2 | DROP / DELETE / TRUNCATE |
| `jdcloud-mongodb-ops` | **required** | 2 | dropDatabase / delete |
| `jdcloud-elasticsearch-ops` | **required** | 2 | delete index / cluster |
| `jdcloud-iam-ops` | **required** | 2 | detach policy / delete role / rotate keys |
| `jdcloud-kms-ops` | **required** | 2 | schedule key deletion is irreversible |
| `jdcloud-eip-ops` | **required** | 2 | release EIP can break production |
| `jdcloud-clb-ops` | recommended | 3 | listener / backend delete |
| `jdcloud-cloudmonitor-ops` | recommended | 3 | alarm rule delete |
| `jdcloud-alert-intelligence` | optional | 5 | read-only |
| `jdcloud-oss-ops` | recommended | 3 | delete bucket / delete object / set public ACL |
| `jdcloud-audit-ops` | optional | 5 | read-only |
| `jdcloud-tag-audit-ops` | optional | 5 | read-only |
| `jdcloud-skill-generator` | optional | 3 | meta operation |
| `jdcloud-disk-ops` | **required** | 2 | delete disk = data loss; resize is expansion-only |
| `jdcloud-fc-ops` | recommended | 3 | delete service cascades functions; throttling risk |
| `jdcloud-waf-ops` | recommended | 3 | delete instance breaks all domain protection |
| `jdcloud-aiops-cruise` | optional | 3 | read-only cruise; Phase 1 sniff + Phase 2 analyze + Phase 3 suggestions (no mutations) |
| `jdcloud-routines-ops` | optional | 3 | read-only by default; on-demand GCL recommended; renewal flows must confirm |
| `jdcloud-billing-ops` | optional | 3 | read-only billing queries; SDK-only |
| `jdcloud-apigateway-ops` | recommended | 3 | API publish / unpublish / delete are reversible but affect live traffic |
| `jdcloud-jcq-ops` | recommended | 3 | topic delete + consumer group reset can lose messages |
| `jdcloud-logservice-ops` | recommended | 3 | index delete is irreversible (data loss); metric/config changes are recoverable |
| `jdcloud-vpn-ops` | recommended | 3 | VPN tunnel delete breaks hybrid cloud connectivity |
| `jdcloud-dns-ops` | recommended | 3 | delete domain removes all records irreversibly; batch set can overwrite all records |
| `jdcloud-cert-ops` | recommended | 3 | delete cert breaks HTTPS for bound CLB/CDN; update cert replaces content |

Each skill may override `max_iter` in its own `SKILL.md` (under `## Quality Gate`).

### 9. Anti-Patterns (banned)

- ❌ **Shared context G+C** — defeats independence → banned
- ❌ **Subjective scoring** — Critic must use the rubric, not "vibes" → banned
- ❌ **Unbounded loop** — always hard-cap iterations → banned
- ❌ **Critic sees the user request** — encourages rubber-stamping → banned
- ❌ **Silently downgrade on Safety fail** — must ABORT visibly → banned
- ❌ **Trace not persisted** — no post-mortem possible → banned
- ❌ **Critic mutates resources** — Critic is read-only by definition → banned
- ❌ **H executes cloud API calls** — H is an offline structural check; calling `jdc` / SDK / mutating anything risks side-effects and contradicts its stateless design → banned
- ❌ **H rewrites G's command** — H must flag hallucinations, not mutate the command. Fixes come from G (re-generation) or the Orchestrator (HALT → manual intervention) → banned
- ❌ **H checks skipped for safety-critical ops** — parameter existence check is MANDATORY for all `required` and `recommended` skills per §8 → banned
- ❌ **Reflexion as mandatory gate** — Pattern retrieval is optional, not a blocking gate → banned
- ❌ **Unbounded Reflexion memory** — Hard cap at 200 lines; prune low-frequency patterns → banned
- ❌ **Subjective pattern extraction** — Patterns must come from structured GCL traces or Self-Review records, not ad-hoc observations → banned

### 10. Hallucination Detection Layer (H) — Phase 6

> **Purpose**: Catch LLM-generated commands, JSON payloads, and architecture suggestions that
> contain structurally invalid elements **before** they reach the cloud API. This is a
> **pre-execution** gate placed between G's generation and actual API execution, filling a
> blind spot the Critic (post-execution) cannot cover.

#### 10.1 Motivation

LLM agents frequently hallucinate when generating JD Cloud CLI commands:

| Hallucination Type | Example | Consequence |
|---|---|---|
| **Non-existent parameter** | `--InstanceId` instead of `--instanceId` (wrong case) | API rejects with InvalidParameter → wasted call + latency |
| **Wrong parameter name** | `--Zone` instead of `--az` | Silent ignore (CLI parses only known flags) → wrong behavior |
| **Non-existent JSON field** | `"Status": "running"` in a response field that should be `"instanceStatus"` | Downstream parse failure |
| **Wrong JSON structure** | Flattened nested objects into a flat map | API rejects or silently ignores fields |
| **Time range violation** | `startTime` > 90 days ago for audit queries | API rejects with InvalidTimeRange |

These are **different from execution errors** caught by the Critic — they are structural
hallucinations that either fail immediately (wasted API call) or, worse, produce a success
response with unintended side effects because a wrong parameter was silently ignored.

#### 10.2 Three-Category Check

##### 10.2.1 CLI Parameter Existence (MANDATORY for all `required`/`recommended` skills)

Verify every `--flag` in the generated command exists in that operation's parameter set.

| Source of Truth | Method | Coverage |
|---|---|---|
| `jdc <product> <operation> --help` | Parse the `--Parameters` section | Production-grade; runnable in CI |
| Skill's `references/api-sdk-usage.md` | Operation map table | Always available offline |
| Built-in parameter knowledge base | Pre-compiled dict in `gcl_runner.py` (`PARAMETER_KNOWLEDGE`) | Default; 300+ operations |

**Algorithm (mechanical H):**

1. Tokenize command into `--flag value` pairs
2. For each `--flag`, look up `(product, operation, flag)` in parameter knowledge base
3. Unrecognized flag → record hallucination
4. All recognized → PASS

**Priority**: Offline knowledge base first → `jdc help` fallback (if CLI available) → PASS
if neither source can confirm (conservative default).

##### 10.2.2 JSON Structure Compliance (RECOMMENDED for JSON-heavy operations)

For operations that pass a JSON payload:

| Check | Rule |
|---|---|
| **Field existence** | Every field in the JSON matches a known OpenAPI field for that operation |
| **Field nesting** | Nested objects match the OpenAPI schema's hierarchy (no flattening) |
| **Type correctness** | Values match expected types: string, integer, boolean, array |
| **Enum membership** | Enum fields use valid values |

**Source of truth**: Skill's `references/api-sdk-usage.md` operation response tables OR a
pre-compiled field map in `gcl_runner.py`.

**Fallback**: If no JSON payload is present in the command, this check passes automatically.

##### 10.2.3 Time Range Validity (MANDATORY for audit-ops)

For audit log queries, ensure time range does not exceed retention limits:

| Check | Rule |
|---|---|
| **Retention limit** | `endTime - startTime ≤ 90 days` (JD Cloud Audit Log retention) |
| **ISO 8601 format** | Both `startTime` and `endTime` are valid ISO 8601 timestamps |
| **Chronological order** | `startTime < endTime` |

**Implementation**: Parse timestamps and compute delta. If delta > 90 days, flag as retention violation.

#### 10.3 Termination

| Condition | Exit Code | Action |
|---|---|---|
| **H_PASS** | — | Continue to [1a] Execute |
| **H_FAIL → Regenerate** | — | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** | 5 | HALT — structural hallucinations persist after regeneration; return unresolved report |

#### 10.4 Trace Integration

The H result is embedded in the GCL trace JSON under `iterations[].hallucination_detector`:

```json
{
  "iterations": [
    {
      "iter": 1,
      "hallucination_detector": {
        "status": "FAIL",
        "checks": {
          "cli_parameters": {
            "total": 4,
            "recognized": 3,
            "unrecognized": ["--Zone"],
            "status": "FAIL"
          },
          "json_structure": {
            "status": "PASS",
            "note": "no JSON payload in command"
          },
          "time_range": {
            "status": "PASS",
            "delta_days": 30,
            "within_retention": true
          }
        },
        "report": "Unrecognized CLI parameter: --Zone (expected alternatives: --az)"
      },
      "regenerated": true,
      "generator": { ... },
      "critic": { ... }
    }
  ]
}
```

#### 10.5 Per-Skill Defaults

Hallucination Detection is **recommended** for all skills, but levels vary:

| GCL Level | Hallucination Check | H Required Dimensions |
|---|---|---|
| **required** | **MANDATORY** | CLI parameter existence + JSON structure (if applicable) |
| **recommended** | **MANDATORY** | CLI parameter existence |
| **optional** | OPTIONAL | None (but recommended for audit-ops: time range validity) |

#### 10.6 Anti-Patterns (H-specific)

See §9 for the full anti-pattern list. H-specific additions:

- H executes cloud API calls — H is an offline structural check; calling `jdc` (or any API) from H
  risks side-effects and contradicts its stateless design
- H rewrites G's command — H must flag hallucinations, not mutate the command. Fixes come from G
  (re-generation) or the Orchestrator (HALT → manual intervention)
- H checks skipped for safety-critical ops — parameter existence is MANDATORY for all `required`
  and `recommended` skills; skipping it for destructive ops defeats the purpose

### 11. Reflexion Integration (Lightweight Reflexion) — Phase 7

> **Purpose**: Enable cross-session learning from failure patterns, complementing the within-session
> GCL loop with persistent failure memory. This is a lightweight adaptation of the Reflexion pattern
> (Shinn et al. 2023) — using structured text files instead of vector memory.

#### 11.1 Motivation

| Gap | Current State | Reflexion Solution |
|-----|---------------|-------------------|
| CLI parameter errors repeat across sessions | §10 documents known patterns, but new patterns aren't auto-captured | Extract from GCL traces → persist in [docs/failure-patterns.md](docs/failure-patterns.md) |
| Skill generation repeats structural issues | Self-Review catches them per-session, but doesn't remember | Record in failure-patterns.md §2 → prevent next generation |
| Cross-skill composition failures | Documented in SKILL.md, but not centralized | Centralize in failure-patterns.md §3 |

#### 11.2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCL Execution (per-session)                   │
│   [0] Pre-flight → [1] Generate → [1.5] H → [2] C → [3] Decide │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    failure_pattern (in trace)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reflexion Memory (cross-session)                    │
│   docs/failure-patterns.md (structured text, ≤200 lines)        │
│   §1 CLI Parameter Errors | §2 Skill Generation | §3 Cross-Skill│
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
│   Agent avoids repeating known mistakes                          │
└─────────────────────────────────────────────────────────────────┘
```

#### 11.3 Failure Pattern Schema

Each pattern in `docs/failure-patterns.md` follows this structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | enum | ✅ | `cli_parameter` \| `skill_generation` \| `cross_skill` \| `runtime` \| `token_efficiency` |
| `skill` | string | ✅ | Skill name (e.g. `jdcloud-audit-ops`) |
| `command` | string | ❌ | The command that failed (for CLI errors) |
| `error` | string | ✅ | Error message or pattern description |
| `fix` | string | ✅ | How to fix or prevent this error |
| `count` | int | ✅ | Frequency count (pruned when < 3) |
| `reusable` | bool | ✅ | Whether this pattern is generalizable |

#### 11.4 Maintenance Rules

| Rule | Description |
|------|-------------|
| **Token budget** | `docs/failure-patterns.md` ≤ 200 lines. When exceeded, prune patterns with `count < 3` |
| **Dedup** | Before adding, check if pattern exists (match by `skill` + `command` + `error`). If exists, increment `count` |
| **Source** | Patterns come from: (1) GCL trace `failure_pattern` field, (2) Self-Review Round 3 Lessons Learned |
| **Review** | Patterns are reviewed monthly. Patterns with `count ≥ 10` are candidates for promotion to §10 Hallucination Detection rules |

#### 11.5 Pre-flight Retrieval (Optional)

During GCL Pre-flight (§4 step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidTimeRange: Limit startTime/endTime ≤ 90 days (retention limit)
- Sensitive data leakage: Apply mask_sensitive() to requestParameters before output
- Large result set timeout: Always use pageNumber/pageSize (≤100) for pagination"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

#### 11.6 Relationship with Other GCL Layers

| Layer | Timing | Learning Scope | Reflexion Complement |
|-------|--------|----------------|---------------------|
| **GCL (Generator-Critic)** | Per-execution | Within-session | — |
| **H (Hallucination Detector)** | Pre-execution | Structural patterns | Reflexion feeds high-frequency H failures into §10 knowledge base |
| **Self-Review (§11)** | Per-update | Skill authoring | Reflexion captures patterns from Self-Review discoveries |
| **Reflexion Memory** | Cross-session | Persistent failure patterns | Aggregates from all above sources |

#### 11.7 Anti-Patterns

- ❌ **Reflexion as mandatory gate** — Pattern retrieval is optional, not a blocking gate
- ❌ **Unbounded memory** — Hard cap at 200 lines; prune low-frequency patterns
- ❌ **Subjective pattern extraction** — Patterns must come from structured GCL traces or Self-Review records, not ad-hoc observations
- ❌ **Pattern hoarding** — If a pattern is promoted to §10 Hallucination Detection rules, remove from failure-patterns.md to avoid duplication

### 12. Rollout Roadmap

- **Phase 1** ✅ — add this section to `AGENTS.md`; pilot on **`jdcloud-vm-ops` only** (most representative
  destructive workload) with its `prompt-templates.md` and `rubric.md`. `jdcloud-redis-ops` follows in the next PR.
- **Phase 2** ✅ — add `scripts/gcl_runner.py` as a reusable Orchestrator
- **Phase 3** ✅ — feed `gcl-trace-*.json` into `jdcloud-audit-ops` for quality dashboards
- **Phase 4** ✅ — wire rubric pass-rate to Cloud Monitor alarms (real incidents refine thresholds)
- **Phase 5** ✅ — GCL rollout extended to all `recommended` skills (CLB, CloudMonitor, OSS, FC, WAF, APIGateway, JCQ, LogService, VPN, DNS, Cert). Each gets lean `references/rubric.md` + `references/prompt-templates.md` + `## Quality Gate (GCL)` section with `max_iter=3`.
- **Phase 6** ✅ — **Hallucination Detection Layer (H)** shipped. §10 added to spec; `scripts/gcl_runner.py` extended with `--enable-hallucination-check` flag and `hallucination_detect()` function (parameter existence, JSON structure, time range validity). Every `required`/`recommended` skill now gets a `HALLUCINATION_ABORT` exit path in addition to the existing `SAFETY_FAIL`.
- **Phase 7** ✅ — **Lightweight Reflexion Integration** shipped. §11 added to spec; `docs/failure-patterns.md` created as centralized Reflexion memory; GCL trace schema extended with `failure_pattern` field; Pre-flight updated with optional pattern retrieval. Cross-session failure pattern learning enabled.
- **Phase 8** ✅ — **jdcloud-audit-ops complete GCL rollout**: Enhanced with 8 dimensions (5 core + 3 Aliyun-specific extensions); added per-operation Safety sub-rules; added worked examples; integrated Phase 6 H layer (optional for audit-ops) and Phase 7 Reflexion; aligned with aliyun-skills GCL v1.9.0 pattern.

### 13. Changelog

| Version | Date | Change |
|---|---|---|
| 1.9.1 | 2026-06-10 | Added `jdcloud-dns-ops` and `jdcloud-cert-ops` skills with full GCL support (recommended, max_iter=3). DNS covers domain/record CRUD, batch operations, monitoring. Cert covers certificate lifecycle and expiry cruise with CLB/CDN cross-service binding discovery. Updated repo layout template to include all 8 reference files. |
| 2.0.0 | 2026-06-18 | **Complete GCL v2 rollout for jdcloud-audit-ops**: Phase 6 (Hallucination Detection Layer H) + Phase 7 (Lightweight Reflexion Integration) fully integrated. Added §10 H layer spec (CLI parameter existence, JSON structure compliance, time range validity); added §11 Reflexion spec (cross-session failure memory via `docs/failure-patterns.md`); enhanced §2 Roles with H role; enhanced §4 Loop Flow with [1.5] H gate; added `HALLUCINATION_ABORT` termination condition; added 6 new anti-patterns (H-specific + Reflexion-specific); updated jdcloud-audit-ops SKILL.md/rubric.md/prompt-templates.md with 8 dimensions (5 core + 3 Aliyun-specific extensions), per-operation Safety sub-rules, worked examples, and H layer prompt template. Aligned with aliyun-skills GCL v1.9.0 pattern. |
| 1.0.0 | 2026-06-04 | Initial GCL specification added to AGENTS.md (Correctness threshold relaxed to ≥0.5; pilot scoped to `jdcloud-vm-ops`) |
| 1.1.0 | 2026-06-04 | `jdcloud-redis-ops` rollout: added `references/rubric.md` and `references/prompt-templates.md`; `## Quality Gate (GCL)` chapter inserted; per-op Safety rules for spec-shrink and cross-instance restore |
| 1.2.0 | 2026-06-04 | `jdcloud-mysql-ops` rollout: rubric expanded to cover DDL/DML paths (instance-level + SQL-level); WHERE-clause check and DDL confirm gates added; prompt templates include pre-check + transaction + affected_rows rules |
| 1.3.0 | 2026-06-04 | `jdcloud-postgresql-ops` rollout: rubric + prompts cover instance + DDL/DML/maintenance paths; PG-specific rules for `VACUUM FULL`, `DROP SCHEMA` cascade, `SELECT FOR UPDATE` re-score |
| 1.3.1 | 2026-06-04 | `jdcloud-mongodb-ops` rollout: rubric + prompts cover instance + DB-level paths; MongoDB-specific rules for `dropDatabase` cascade, `updateMany` empty-filter check, `$out`/`$merge` in aggregate |
| 1.3.2 | 2026-06-04 | `jdcloud-elasticsearch-ops` rollout: rubric + prompts cover instance + ES REST paths; ES-specific rules for wildcard `DELETE /<index>`, `match_all` in `_update_by_query`/`_delete_by_query`, `_forcemerge max_num_segments=1` |
| 1.4.0 | 2026-06-04 | `jdcloud-iam-ops` rollout: rubric + prompts cover sub-user, group, role, policy, access-key, STS; IAM-specific rules for `attach AdministratorAccess` / `*:*`, `create main-account key`, `delete sub-user` with attached policies, `Principal: *` trust policy; **secret value never logged** |
| 1.4.1 | 2026-06-04 | `jdcloud-kms-ops` rollout: rubric + prompts cover key lifecycle, encrypt/decrypt, secret; KMS-specific rules for irreversible `schedule key deletion`, `pending-window-in-days` min-7 guard, prod `disable` / `decrypt` confirm; **plaintext / secret value never logged** (SHA-256 + length only) |
| 1.4.2 | 2026-06-04 | `jdcloud-eip-ops` rollout: rubric + prompts cover allocate, associate, dissociate, release; EIP-specific rules for irreversible `release EIP` (InUse refusal), prod `dissociate` / `release` confirm, `associate` force-rebind guard |
| 1.5.0 | 2026-06-04 | `jdcloud-clb-ops` rollout (recommended, max_iter=3): rubric + prompts cover LB, listener, target register/deregister, health check; CLB-specific rules for `delete-lb` traffic cut, `deregister-targets` >50% DRAIN guard, `register-targets` non-running backend refusal |
| 1.5.1 | 2026-06-04 | `jdcloud-cloudmonitor-ops` rollout (recommended, max_iter=3): rubric + prompts cover alarm rule CRUD + metric query; silent-failure guards for `delete-alarm-rule` / `disable-alarm-rule`, `DELETE_AFTER_FIRING` rule, prod tag double-confirm, empty notification channel refusal |
| 1.6.0 | 2026-06-04 | `jdcloud-alert-intelligence` rollout (optional, max_iter=5, read-only): rubric enforces "report must NOT recommend delete/disable/modify on alert rule" + 4-tuple citation + next-hop suggestion; PII / secret mask |
| 1.6.1 | 2026-06-04 | `jdcloud-audit-ops` rollout (optional, max_iter=5, read-only): rubric + prompts cover `describe-events` / `describe-event-detail` / `describe-trails`; PII masking guard for `requestParameters` (password / secret / accessKey) |
| 1.6.2 | 2026-06-04 | `jdcloud-tag-audit-ops` rollout (optional, max_iter=5): rubric + prompts cover audit + report + DOPS ticket creation; DOPS ticket payload completeness + duplicate-ticket idempotency check |
| 1.6.3 | 2026-06-04 | `jdcloud-skill-generator` rollout (optional, max_iter=3, meta): rubric + prompts cover generation steps; secret-leak guard, OpenSpec + 2-round self-review enforcement, jdc CLI / SDK cross-validation |
| 1.7.0 | 2026-06-08 | `jdcloud-oss-ops` rollout: SDK-only SKILL.md (OSS not exposed via `jdc` CLI); rubric + prompts cover bucket CRUD, object CRUD, ACL, lifecycle, versioning, CRR, presigned URL; safety gates for delete bucket/object, public ACL on prod |
| 1.8.0 | 2026-06-08 | `jdcloud-disk-ops` rollout (required, max_iter=2): dual-path SKILL.md; rubric + prompts cover disk CRUD, attach/detach, resize, snapshot, backup policy; safety gates for delete disk with in-use check, resize shrink prevention, system disk detach guard |
| 1.8.1 | 2026-06-08 | `jdcloud-fc-ops` rollout (recommended, max_iter=3): SDK-only SKILL.md (FC not exposed via `jdc` CLI); rubric + prompts cover service/function CRUD, invoke, version/alias, triggers; safety gates for delete service cascade, prod invoke confirm, runtime/handler validation |
| 1.8.2 | 2026-06-08 | `jdcloud-waf-ops` rollout (recommended, max_iter=3): dual-path SKILL.md; rubric + prompts cover WAF instance/domain/rule CRUD, SSL cert, bot management, attack logs; safety gates for delete instance with domain check, disable domain origin-exposure warning, cert-domain mismatch guard |
| 1.9.1 | 2026-06-10 | Added `jdcloud-billing-ops` skill: balance, consumption, bill details, vouchers, cost estimation; SDK-only billing operations; updated `jdcloud-routines-ops` to delegate billing to billing-ops; updated AGENTS.md cross-skill delegation table |
| 1.9.0 | 2026-06-10 | **AI OPS 系统性评审批次**: `jdcloud-aiops-cruise` v1.4.0 → **v1.5.0** (optional/read-only, max_iter=3, 8/8 refs 补齐, Quality Gate GCL 章节 +56 行), `jdcloud-alert-intelligence` v0.2.0 → **v0.3.0** (optional, max_iter=5, R1/R2/R3 口径同步, 8/8 refs 补齐, +4 new refs), `jdcloud-cloudmonitor-ops` v1.4.0 → **v1.5.0** (recommended, max_iter=3, 9/9 refs 完整, GCL 章节整合, parent_skill/ecosystem_skills 元数据), `jdcloud-routines-ops` v1.0.0 → **v1.1.0** (optional, max_iter=3, 8/8 refs 补齐, 职责边界表 + Cross-Skill Delegation 表新增, GCL optional); Cross-Skill Delegation 表追加 aiops-cruise / alert-intelligence / routines-ops / eip-ops / disk-ops / fc-ops / waf-ops / apigateway-ops / tag-audit-ops / audit-ops / logservice-ops 入口; 新增 `tests/test_aiops_consistency.py` (dry-run 一致性检查) + `.github/workflows/aiops-audit.yml` (CI workflow 草案) |

## 13. See also

- [`docs/GCL_RETROSPECTIVE.md`](docs/GCL_RETROSPECTIVE.md) — post-rollout retrospective and Phase 3 dashboard design contract (2026-06-04)
- Each skill's `references/rubric.md` — the rubric instance
- Each skill's `references/prompt-templates.md` — the G/C/O prompt skeletons

---

## 14. Karpathy Guidelines

> Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876).
> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 14.1 Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 14.2 Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 14.3 Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 14.4 Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.