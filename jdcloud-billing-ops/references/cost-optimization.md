# Cost Optimization — JD Cloud Billing

## Overview

综合考虑代金券（到期时间、余额、适用范围）、账户余额、计费方式（预付费/后付费）
等因素，输出**多方案对比**供用户决策。帮助用户在续费、新购、迁移场景中找到
最节省的支付方案。

## Data Sources

| 数据 | Service | Request Class | Key Fields |
|------|---------|---------------|------------|
| 账户余额 | `asset` | `DescribeAccountAmountRequest` | `totalAmount`, `availableAmount` |
| 代金券列表 | `instancevoucher` | `DescribeInstanceVouchersRequest` | `voucherId`, `name`, `status`, `balance`, `expireTime` |
| 资源询价 | `billing` | `CalculateTotalPriceRequest` | `totalPrice`, `discountedTotalPrice`, `totalOriginalPrice` |
| 消费汇总 | `billing` | `QueryBillSummaryRequest` | `totalFee`, `discountFee`, `realTotalFee` |

## Optimization Strategies

### 方案A: 代金券优先（防过期）

**策略**: 优先使用即将到期的代金券支付，避免过期浪费。

```
1. 查询所有 active 代金券，按 expireTime 升序排列
2. 筛选出 expireTime < 30 天的代金券
3. 优先用这些代金券支付续费/新购费用
4. 余额不足部分用账户余额补齐
```

**适用场景**: 有大量即将到期代金券、资源必须续费

### 方案B: 余额+代金券组合最优

**策略**: 结合代金券使用限制和余额，最大化节省现金支出。

```
1. 查询代金券列表，检查 productScope（适用产品）
2. 按 productScope 匹配目标资源
3. 匹配的代金券优先使用，不匹配的保留
4. 余额用于支付代金券覆盖不足的部分
5. 保留部分余额作为缓冲
```

**适用场景**: 代金券有产品限制、需要保留余额缓冲

### 方案C: 预付费 vs 后付费对比

**策略**: 对比预付费折扣和后付费灵活性，选择最优计费方式。

```
1. 查询目标资源按需（后付费）价格
2. 查询预付费价格（1个月/3个月/6个月/1年）
3. 计算预付费折扣率
4. 对比：预付费节省金额 vs 资金占用成本
5. 结合代金券可用性调整方案
```

**适用场景**: 新购资源、长期运行资源、大促窗口期

## Multi-Plan Comparison

### 示例：续费一台 VM（c.n1.large, 1年）

| 方案 | 原价 | 代金券抵扣 | 余额支付 | 实际支出 | 节省率 | 风险 |
|------|------|-----------|---------|---------|-------|------|
| A: 代金券优先 | ¥6,000 | ¥2,000（即将到期） | ¥4,000 | **¥4,000** | **33%** | 代金券用完，后续无券 |
| B: 组合最优 | ¥6,000 | ¥1,000（匹配产品） | ¥5,000 | **¥5,000** | 17% | 保留 ¥1,000 券备用 |
| C: 预付费 | ¥6,000 | — | ¥4,800（8折） | **¥4,800** | 20% | 预付费不可退款 |
| D: 后付费（1年） | ¥7,200 | ¥2,000（即将到期） | ¥5,200 | **¥5,200** | 28% | 灵活但总价高 |

**推荐**: 方案A（代金券即将过期时）或方案C（无代金券时）

### 决策启发式

```
用户有即将到期代金券？
  ├─ 是 → 方案A（优先用券防过期）
  └─ 否 → 代金券匹配目标产品？
           ├─ 是 → 方案B（组合最优）
           └─ 否 → 资源长期运行？
                    ├─ 是 → 方案C（预付费折扣）
                    └─ 否 → 后付费（按需）
```

## Executable Scripts

The plan analysis functions are available as an importable Python module:

```bash
# Run with mock data (demo)
python scripts/cost_optimizer.py

# Run with mock data, JSON output
python scripts/cost_optimizer.py --json

# Import in your own code
from scripts.cost_optimizer import (
    plan_a_voucher_first,
    plan_b_combined,
    plan_c_prepaid,
    present_plans,
)
```

See [`scripts/cost_optimizer.py`](../scripts/cost_optimizer.py) for the full implementation.

## Integration with SKILL.md

This reference is used by `jdcloud-billing-ops/SKILL.md` in the **智能成本优化方案**
flow. The orchestrator agent:

1. Gathers balance + vouchers + price data via SDK
2. Runs plan analysis (A/B/C)
3. Presents comparison table to user
4. User selects and confirms a plan
5. Delegates execution to the appropriate ops skill

> **Note**: This skill is **read-only**. The orchestrator outputs comparison plans
> and recommendations. Actual resource operations (续费/新购) are delegated to
> product-specific ops skills after user confirmation.

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-10 | Initial release: multi-plan comparison (voucher-first, combined, prepaid vs postpaid) |
