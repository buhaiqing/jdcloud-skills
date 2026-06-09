---
name: jdcloud-routines-ops
version: "1.0.0"
metadata:
  displayName: 京东云日常运维
  description: 京东云日常运维场景集：资源到期巡检、账单分析、资源盘点等
  icon: 🔧
  tags: [jdcloud, operations, routines, cruise, expiry]
  cli_applicability: jdc + SDK
  cli_version_locked: "1.2.12"
  sdk_version_locked: ""
---

## Overview

`jdcloud-routines-ops` 是京东云日常运维场景的集 Skill，提供资源到期巡检、资源盘点等常用运维能力。

### 支持场景

| 场景 | 说明 | 状态 |
|------|------|------|
| [资源到期巡检](#资源到期巡检) | 巡检VM/云盘/EIP/Redis/RDS/CLB/MongoDB/Elasticsearch/SSL证书等资源到期情况 | ✅ 可用 |
| [资源账单分析](#资源账单分析) | 分析各客户的资源费用支出 | 🔜规划中 |
| [资源盘点报告](#资源盘点报告) | 生成客户资源使用汇总报告 | 🔜 规划中 |

---

## Variable Convention

| 类型 | 语法 | 示例 | 说明 |
|------|------|------|------|
| 运行时 | `{{env.*}}` | `{{env.JDC_ACCESS_KEY}}` | agent 运行时变量 |
| 用户输入 | `{{user.*}}` | `{{user.customer}}` | 需用户确认的参数 |
| 输出引用 | `{{output.*}}` | `{{output.report_path}}` | 脚本输出路径 |

---

## 资源到期巡检

### Description

巡检当前账号下所有区域的资源（VM、云盘、EIP、Redis、RDS、CLB、MongoDB、Elasticsearch、SSL证书等）的到期情况，按客户分组展示。

### Parameters

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--warning-days` | int | `14` | 预警天数阈值（默认14天内到期） |
| `--regions` | string | `all` | 巡检区域，逗号分隔或 `all` |
| `--types` | string | `vm,redis,eip,disk,rds,clb,mongodb,elasticsearch,ssl` | 资源类型，逗号分隔 |
| `--customer` | string | `` | 按客户名称过滤（可选） |
| `--output-dir` | string | `~/.jdcloud-routines-ops/outputs` | 输出目录 |

### Execution Flow

```
1. Pre-flight
   ├── 激活 .venv (Python 3.10)
   ├── 解析参数（warning-days, regions, types）
   └── 确认 jdc CLI凭证可用

2. Execute (jdc primary)
   ├── 遍历指定区域
   │ ├── vm describe-instances
   │   ├── redis describe-cache-instances
   │   ├── disk describe-disks
   │   ├── vpc describe-eips
   │   ├── rds describe-instances
   │   ├── lb describe-load-balancers
   │   ├── mongodb describe-instances
   │   └── elasticsearch (SDK OpenAPI)
   ├── SSL 证书全局巡检（不分区域）
   │   └── ssl describe-certs
   └── 解析 chargeExpiredTime，计算剩余天数

3. Output
   ├── 控制台彩色输出汇总
   ├── JSON 详细报告 → outputs/expiry/YYYYMMDD-HHMMSS.json
   └── 返回0 (有到期资源) 或 1 (无到期资源)
```

### Output Parsing

| 资源类型 | jdc 命令 | 到期字段 |
|----------|----------|----------|
| VM | `vm describe-instances` | `$.result.instances[].charge.chargeExpiredTime` |
| Redis | `redis describe-cache-instances` | `$.result.cacheInstances[].charge.chargeExpiredTime` |
| 云盘 | `disk describe-disks` | `$.result.disks[].charge.chargeExpiredTime` |
| EIP | `vpc describe-eips` | `$.result.eips[].charge.chargeExpiredTime` |
| RDS | `rds describe-instances` | `$.result.dbInstances[].charge.chargeExpiredTime` |
| CLB | `lb describe-load-balancers` | `$.result.loadBalancers[].charge.chargeExpiredTime` |
| MongoDB | `mongodb describe-instances` | `$.result.mongodbInstances[].charge.chargeExpiredTime` |
| Elasticsearch | SDK OpenAPI | `$.result.instances[].charge.chargeExpiredTime` |
| SSL证书 | `ssl describe-certs` | `$.result.certListDetails[].endTime` |

### Example

```bash
# 基本巡检（14天阈值，所有区域）
python jdcloud-routines-ops/scripts/expiry_cruise.py

# 7天紧急预警
python jdcloud-routines-ops/scripts/expiry_cruise.py --warning-days 7

# 只巡检华北区域和VM类型
python jdcloud-routines-ops/scripts/expiry_cruise.py --regions cn-north-1 --types vm

# 只巡检华北区域和RDS类型
python jdcloud-routines-ops/scripts/expiry_cruise.py --regions cn-north-1 --types rds

# 只巡检SSL证书（全局资源）
python jdcloud-routines-ops/scripts/expiry_cruise.py --types ssl

# 按客户过滤
python jdcloud-routines-ops/scripts/expiry_cruise.py --customer 烟台振华
```

### Output Artifacts

| 文件 | 路径 | 说明 |
|------|------|------|
| 控制台摘要 | stdout | 按客户分组的到期资源列表 |
| JSON 报告 | `outputs/expiry/expiry-report-YYYYMMDD-HHMMSS.json` | 完整数据，可供后续处理 |

---

## 资源账单分析

> 🔜 规划中

分析各客户的资源费用支出，支持按月汇总、按资源类型分组。

---

## 资源盘点报告

> 🔜 规划中

生成客户资源使用汇总报告，包括VM规格、存储容量、网络配置等。

---

## Output Management

### 目录结构

```
~/.jdcloud-routines-ops/
└── outputs/
    └── expiry/
        └── expiry-report-20260609-143000.json
```

### 清理策略

```bash
# 清理7天前的报告
find ~/.jdcloud-routines-ops/outputs -type f -mtime +7 -delete

# 清理30天前的报告
find ~/.jdcloud-routines-ops/outputs -type f -mtime +30 -delete
```

### .gitignore

项目内 `outputs/` 目录已加入 `.gitignore`，不会提交到 git repo。

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.5.0 | 2026-06-09 | 添加 MongoDB 和 Elasticsearch 到期巡检；默认 types 增加 mongodb,elasticsearch |
| 1.4.0 | 2026-06-09 | 添加 CLB 负载均衡到期巡检；默认 types 增加 clb |
| 1.3.0 | 2026-06-09 | 添加 SSL 证书到期巡检；汇总报告增加区域统计 |
| 1.2.0 | 2026-06-09 | 添加 RDS 到期巡检（支持 MySQL/PostgreSQL/SQL Server） |
| 1.0.0 | 2026-06-09 | Initial release with expiry cruise scenario |