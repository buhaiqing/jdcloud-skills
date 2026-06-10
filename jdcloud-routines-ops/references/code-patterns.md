# Code Patterns — `jdcloud-routines-ops`

> **目标读者：LLM Agent**。本文档提供脚本开发的模式模板，让 Agent 在面对新场景
> （询价、账单分析、资源盘点）时，从"反复试错"变为"套用模板"。
>
> 每个模式包含：**适用场景 → 模板代码 → 关键要点 → 反模式**。

---

## 模式 1：资源迭代通用模板（配置驱动）

**适用场景**：需要对多种资源类型（VM/Redis/RDS/CLB/...）执行相同逻辑时。

**核心思想**：用配置表替代 8 个重复函数，新增资源类型只需加一行配置。

### 模板

```python
# 资源类型配置表：定义每种资源的 API、字段路径、输出格式
RESOURCE_CONFIG = {
    "vm": {
        "api": "describe_vms",
        "list_key": "instances",
        "id_key": "instanceId",
        "name_key": "instanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {"instance_type": "instanceType"},
    },
    "redis": {
        "api": "describe_redis",
        "list_key": "cacheInstances",
        "id_key": "cacheInstanceId",
        "name_key": "cacheInstanceName",
        "charge_path": ["charge", "chargeExpiredTime"],
        "extra_fields": {"memory_mb": "cacheInstanceMemoryMB"},
    },
    # 新增资源类型只需在此加一行配置
}

def cruise_resource(client, resource_type, region, filter_fn, format_fn):
    """通用资源巡检 — 所有资源类型复用此模板"""
    cfg = RESOURCE_CONFIG[resource_type]
    items = getattr(client, cfg["api"])(region)
    results = []
    for item in items:
        if not filter_fn(item, cfg):
            continue
        results.append(format_fn(item, cfg, region))
    return results
```

### 关键要点

- `RESOURCE_CONFIG` 是**唯一需要修改的地方**，不要为每个资源类型写新函数
- `filter_fn` 和 `format_fn` 是通用逻辑，所有资源类型共享
- `extra_fields` 用 `{输出字段名: API响应字段名}` 映射

### 反模式

```python
# ❌ 不要这样做：为每个资源类型复制几乎相同的函数
def cruise_vm(client, ...):    # 50 行
def cruise_redis(client, ...): # 50 行（99% 相同）
def cruise_rds(client, ...):   # 50 行（99% 相同）
# ... 8 个函数，维护噩梦
```

---

## 模式 2：`--input-json` 复杂参数传递

**适用场景**：调用 `jdc billing`、`jdc renewal` 等需要传入嵌套 JSON 结构的 API。

**核心思想**：`--input-json` 是 jdc CLI 处理复杂参数的**唯一正确方式**，
不要尝试用 `--order-list '[...]'` 等命令行参数传递嵌套结构。

### 模板

```python
def call_jdc_with_input_json(subcommand: str, payload: dict,
                              region: str = None) -> dict:
    """调用需要 --input-json 的 jdc 命令。

    适用场景：
      - jdc billing calculate-total-price  （询价）
      - jdc renewal renew-instance          （续费）
      - 任何需要传入嵌套 JSON 结构的 API

    Args:
        subcommand: jdc 子命令，如 "billing calculate-total-price"
        payload: 完整的 JSON 请求体
        region: 区域 ID（可选）

    Returns:
        API 响应的 result 字段
    """
    args = subcommand.split()
    if region:
        args.extend(["--region-id", region])

    # 关键：用 --input-json 传入 JSON 字符串，不是 --order-list 等
    args.extend(["--input-json", json.dumps(payload, ensure_ascii=False)])

    result = client.run(args)
    return result.get("result", {})


# 使用示例：询价
order_payload = {
    "cmd": 2,              # 1=创建 2=续费 3=升配 4=删除
    "packageCount": 1,
    "orderList": [{
        "serviceCode": "vm",
        "resourceId": "i-xxx",
        "billingType": 1,  # 1=包年包月
        "timeSpan": 1,
        "timeUnit": 2,     # 2=月
        "formula": "...",  # 从 renewal query-instance 获取
        "count": 1,
    }]
}
price = call_jdc_with_input_json(
    "billing calculate-total-price", order_payload, region="cn-north-1"
)
```

### 关键要点

- `--input-json` 必须在 `jdc` 命令中作为**最后一个参数**
- payload 中的嵌套结构（如 `orderList[].formula`）直接传 JSON，不需要转义
- `cmd` 枚举：1=创建 2=续费 3=升配 4=删除

### 反模式

```bash
# ❌ 不要这样做：用 --order-list 传 JSON 字符串
jdc billing calculate-total-price --cmd 2 --package-count 1 \
  --order-list '[{"serviceCode":"vm",...}]'   # 会报参数解析错误

# ❌ 不要这样做：用 shell 变量拼接 JSON
ORDER_JSON='[{"serviceCode":"vm",...}]'
jdc billing calculate-total-price --cmd 2 --order-list "$ORDER_JSON"
```

---

## 模式 3：多步骤依赖流程（询价/续费核心）

**适用场景**：需要先查询 A 获取数据，再用 A 的结果调用 B 的场景。

**核心思想**：询价不是单步 API 调用，而是 `renewal.query-instance` →
`billing.calculate-total-price` 的**两步依赖流程**。

### 模板

```python
def price_inquiry_for_resource(client, resource_type: str, resource_id: str,
                                region: str, renew_months: int = 1) -> dict:
    """询价流程：查询可续费实例 → 构造订单 → 调用询价 API

    这是 billing 相关脚本的核心流程模板。所有需要询价的场景
    （到期巡检后的续费预估、账单分析中的费用预测）都复用此模板。

    Args:
        client: JdcClient 实例
        resource_type: 资源类型（vm/redis/rds/disk/eip/clb/mongodb/es）
        resource_id: 资源 ID
        region: 区域
        renew_months: 续费月数

    Returns:
        {
            "resource_id": "i-xxx",
            "resource_type": "vm",
            "original_price": 123.45,    # 原价
            "discount_price": 98.76,     # 折扣价
            "total_price": 98.76,        # 实付价
            "renew_months": 1,
        }
    """

    # ── Step 1: 查询可续费实例信息 ──
    # 从 renewal API 获取 formula（计费公式）和 billingType
    instances = client.run([
        "renewal", "query-instance",
        "--region-id", region,
        "--service-code", resource_type,
        "--resource-id", resource_id,
    ])
    instance_list = instances.get("result", {}).get("list", [])
    if not instance_list:
        return {"error": f"资源 {resource_id} 不可续费或不存在"}

    instance_info = instance_list[0]

    # ── Step 2: 构造询价订单 ──
    order_payload = {
        "cmd": 2,              # 2 = 续费
        "packageCount": 1,
        "orderList": [{
            "serviceCode": resource_type,
            "resourceId": resource_id,
            "billingType": instance_info.get("billingType", 1),
            "timeSpan": renew_months,
            "timeUnit": 2,     # 2 = 月
            "formula": instance_info.get("formula", ""),
            "count": 1,
        }]
    }

    # ── Step 3: 调用询价 API ──
    price_result = client.run([
        "billing", "calculate-total-price",
        "--region-id", region,
        "--input-json", json.dumps(order_payload),
    ])
    price_data = price_result.get("result", {})

    return {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "original_price": price_data.get("totalPrice", 0),
        "discount_price": price_data.get("discountPrice", 0),
        "total_price": price_data.get("totalPrice", 0),
        "renew_months": renew_months,
    }


def batch_price_inquiry(client, resources: list[dict],
                         renew_months: int = 1) -> list[dict]:
    """批量询价：对到期巡检结果中的资源列表逐一询价

    Args:
        client: JdcClient 实例
        resources: 到期巡检结果列表，每项含 type/id/region
        renew_months: 续费月数

    Returns:
        询价结果列表，按 total_price 降序排列
    """
    results = []
    for r in resources:
        price = price_inquiry_for_resource(
            client, r["type"], r["id"], r["region"], renew_months
        )
        if "error" not in price:
            # 合并原始资源信息
            price["name"] = r.get("name", "")
            price["customer"] = r.get("customer", "")
            price["days_left"] = r.get("days_left", 0)
            results.append(price)

    # 按价格降序排列
    results.sort(key=lambda x: x["total_price"], reverse=True)
    return results
```

### 关键要点

- **Step 1 不可跳过**：`formula` 字段必须从 `renewal.query-instance` 获取，不能硬编码
- **Step 2 的 `cmd` 枚举**：1=创建 2=续费 3=升配 4=删除
- **Step 3 的 `timeUnit` 枚举**：1=小时 2=月 3=年
- 批量询价时建议**串行调用**（避免触发 API 限流），如需并发则加 `time.sleep(0.5)` 间隔

### 反模式

```python
# ❌ 不要这样做：跳过 Step 1，硬编码 formula
order_payload = {
    "orderList": [{
        "formula": "vm.m.n2.xlarge * 1",  # 硬编码，不同资源 formula 不同
        ...
    }]
}

# ❌ 不要这样做：用错误的 cmd 值
order_payload = {"cmd": 1, ...}  # 1=创建，不是续费！续费应该用 cmd=2
```

---

## 模式 4：jdc-first with SDK Fallback 标准写法

**适用场景**：所有需要调用 JD Cloud API 的脚本。

**核心思想**：统一 jdc-first 策略的实现，消除项目中两个 `jdc_client.py`
使用不同底层实现的歧义。

### 模板

```python
def call_api(client, resource_type: str, action: str, region: str,
             extra_args: list = None, max_retries: int = 3) -> dict:
    """jdc-first with SDK fallback 标准调用

    策略：
      1. 尝试 jdc CLI（最多 max_retries 次，指数退避）
      2. 全部失败后 fallback 到 SDK
      3. 返回统一格式的 result

    Args:
        client: JdcClient 实例
        resource_type: 资源类型（vm/redis/rds/...）
        action: API 动作（describe-instances/describe-cache-instances/...）
        region: 区域 ID
        extra_args: 额外 CLI 参数列表
        max_retries: CLI 最大重试次数

    Returns:
        API 响应的 result 字段
    """
    import time

    base_args = [resource_type, action, "--region-id", region]
    if extra_args:
        base_args.extend(extra_args)

    # ── 尝试 jdc CLI ──
    last_error = None
    for attempt in range(max_retries):
        try:
            result = client.run(base_args)
            if "error" not in result:
                return result.get("result", {})
            last_error = result["error"]
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # 0s → 2s → 4s

    # ── SDK fallback ──
    # 仅在 jdc CLI 3 次全部失败时使用
    # 具体 SDK 调用逻辑见各资源类型的 _sdk_fallback_* 函数
    raise RuntimeError(
        f"jdc CLI failed after {max_retries} attempts: {last_error}. "
        f"SDK fallback not implemented for {resource_type}/{action}."
    )
```

### 关键要点

- 重试间隔用 `2 ** attempt`（0s → 2s → 4s），符合 AGENTS.md 规范
- 只在 `result` 不含 `"error"` 键时认为成功
- SDK fallback 是**最后手段**，不要优先使用 SDK
- 两个 `jdc_client.py` 的区别：
  - `routines-ops/lib/jdc_client.py`：基于 `subprocess.run(["jdc", ...])`，适合简单 describe
  - `aiops-cruise/lib/jdc_client.py`：基于 `urllib` + 手动签名，适合复杂 API + 自动分页
  - **本 skill 脚本统一使用 `routines-ops/lib/jdc_client.py`**

### 反模式

```python
# ❌ 不要这样做：直接使用 SDK 而不尝试 jdc CLI
from jdcloud_sdk.services.vm.client.VmClient import VmClient
client = VmClient(credential)
vms = client.send(...)  # 跳过了 jdc-first 策略

# ❌ 不要这样做：混合使用两个 jdc_client
from lib.jdc_client import JdcClient  # routines-ops 版本
# ... 然后又 import aiops-cruise 的 JdcClient
```

---

## 模式 5：报告输出模板（控制台 + JSON 双输出）

**适用场景**：所有巡检/分析脚本的输出环节。

**核心思想**：统一报告格式，确保控制台可读 + JSON 可机器处理。

### 模板

```python
def output_report(data: list[dict], output_dir: Path, report_type: str,
                   summary_extra: dict = None) -> Path:
    """统一报告输出：控制台彩色 + JSON 文件

    Args:
        data: 结果列表，每项为 dict
        output_dir: 输出目录
        report_type: 报告类型标识（expiry/price/inventory）
        summary_extra: 额外汇总字段（如 total_price、customer_count）

    Returns:
        报告文件路径
    """
    from collections import defaultdict
    from datetime import datetime

    # ── 控制台输出 ──
    if not data:
        print(f"\n✅ 无数据，跳过报告生成")
        return None

    # 按客户分组
    by_customer = defaultdict(list)
    for r in data:
        by_customer[r.get("customer", "未知")].append(r)

    print(f"\n{'='*60}")
    print(f"📊 {report_type} 报告")
    print(f"{'='*60}")

    for customer, items in sorted(by_customer.items(),
                                   key=lambda x: -len(x[1])):
        print(f"\n🏢 {customer} ({len(items)} 项)")
        for item in items:
            # 子类可覆盖此格式化逻辑
            print(format_item(item))

    # ── JSON 落盘 ──
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = output_dir / f"{report_type}-{timestamp}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建汇总
    summary = {
        "total_count": len(data),
        "customer_count": len(by_customer),
        "by_customer": {k: len(v) for k, v in by_customer.items()},
    }
    if summary_extra:
        summary.update(summary_extra)

    report = {
        "report_time": datetime.now().isoformat(),
        "report_type": report_type,
        "summary": summary,
        "details": data,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 报告已保存: {report_path}")
    return report_path


def format_item(item: dict) -> str:
    """格式化单条结果（子类可覆盖）"""
    urgency = "🔴" if item.get("days_left", 999) <= 3 else \
              ("🟡" if item.get("days_left", 999) <= 7 else "🟢")
    return (
        f"   {urgency} [{item.get('type', '?')}] {item.get('name', '?')}\n"
        f"       区域: {item.get('region', '?')} | "
        f"剩余 {item.get('days_left', '?')} 天"
    )


# ──────────────────────────────────────────────
# 6. 快速开始：完整脚本骨架
# ──────────────────────────────────────────────

def main():
    """完整脚本骨架： expiry_cruise / price_inquiry / billing_analysis 都基于此结构"""
    import argparse
    from pathlib import Path

    # 1. 解析参数
    parser = argparse.ArgumentParser(description="JD Cloud 资源巡检脚本")
    parser.add_argument("--regions", default="cn-north-1", help="区域列表")
    parser.add_argument("--output-dir", default="./outputs", help="输出目录")
    parser.add_argument("--customer", default="", help="客户过滤")
    args = parser.parse_args()

    # 2. 初始化客户端
    client = JdcClient()  # 从 lib.jdc_client 导入

    # 3. 遍历区域和资源类型
    all_results = []
    for region in args.regions.split(","):
        for resource_type in RESOURCE_CONFIG.keys():
            results = cruise_resource(
                client, resource_type, region,
                filter_fn=lambda item, cfg: apply_customer_filter(item, args.customer),
                format_fn=format_item  # 或 resource_type 特定的 formatter
            )
            all_results.extend(results)

    # 4. 输出报告
    output_report(
        data=all_results,
        output_dir=Path(args.output_dir),
        report_type="expiry",  # 或 "price" / "billing"
        summary_extra={"total_resources": len(all_results)}
    )


if __name__ == "__main__":
    main()
"
        f"