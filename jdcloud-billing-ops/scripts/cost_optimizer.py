#!/usr/bin/env python3
"""JD Cloud cost optimization: multi-plan comparison (voucher-first, combined, prepaid).

Extracts the plan_a/b/c analysis functions from cost-optimization.md into
executable code.  Run directly for a demo with mock data, or import and use
with real SDK responses.

Usage:
    python scripts/cost_optimizer.py                          # mock demo
    python scripts/cost_optimizer.py --real                    # (future) real SDK path
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from typing import Any


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_iso(s: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string, tolerating trailing 'Z'."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _try_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ── plan functions (from cost-optimization.md) ───────────────────────────────


def plan_a_voucher_first(
    vouchers: list[Any],
    total_price: float,
    balance: float,
    urgent_days: int = 30,
) -> dict[str, Any]:
    """方案A: 优先使用即将到期的代金券.

    Args:
        urgent_days: 到期预警天数（默认 30，可通过 config.yaml 调整）
    """
    now = datetime.now()
    cutoff = now + timedelta(days=urgent_days)
    urgent_vouchers = [
        v
        for v in vouchers
        if hasattr(v, "expireTime")
        and v.expireTime
        and (exp := _parse_iso(v.expireTime)) is not None
        and exp < cutoff
    ]
    urgent_vouchers.sort(key=lambda v: v.expireTime or "")

    voucher_deduction = 0.0
    for v in urgent_vouchers:
        remaining = total_price - voucher_deduction
        if remaining <= 0:
            break
        voucher_deduction += min(_try_float(v.balance), remaining)

    balance_needed = max(0.0, total_price - voucher_deduction)
    cash_out = max(0.0, balance_needed - balance)

    return {
        "name": "A: 代金券优先（防过期）",
        "original": total_price,
        "voucher_used": round(voucher_deduction, 2),
        "balance_used": round(min(balance_needed, balance), 2),
        "cash_needed": round(cash_out, 2),
        "savings": round(voucher_deduction / total_price * 100, 1) if total_price else 0.0,
        "risk": "代金券用完，后续无券可用",
    }


def plan_b_combined(
    vouchers: list[Any],
    total_price: float,
    balance: float,
    buffer_ratio: float = 0.2,
) -> dict[str, Any]:
    """方案B: 余额+代金券组合最优.

    Args:
        buffer_ratio: 余额缓冲比例（默认 0.2 = 保留 20%）
    """
    matched_vouchers = [
        v for v in vouchers if hasattr(v, "status") and v.status == "active"
    ]

    voucher_deduction = 0.0
    for v in matched_vouchers:
        remaining = total_price - voucher_deduction
        if remaining <= 0:
            break
        voucher_deduction += min(_try_float(v.balance), remaining)

    balance_needed = max(0.0, total_price - voucher_deduction)
    balance_usable = max(0.0, balance * (1 - buffer_ratio))
    balance_use = min(balance_usable, balance_needed)
    cash_out = max(0.0, balance_needed - balance_use)

    return {
        "name": "B: 组合最优",
        "original": total_price,
        "voucher_used": round(voucher_deduction, 2),
        "balance_used": round(balance_use, 2),
        "cash_needed": round(cash_out, 2),
        "savings": round(voucher_deduction / total_price * 100, 1) if total_price else 0.0,
        "risk": f"保留 {int(buffer_ratio * 100)}% 余额缓冲",
    }


def plan_c_prepaid(
    original_price: float,
    total_price: float,
    balance: float,
) -> dict[str, Any]:
    """方案C: 预付费 vs 后付费."""
    savings = original_price - total_price
    savings_rate = savings / original_price * 100 if original_price else 0.0
    cash_needed = max(0.0, total_price - balance)

    return {
        "name": "C: 预付费折扣",
        "original": original_price,
        "discounted": total_price,
        "balance_used": round(min(total_price, balance), 2),
        "cash_needed": round(cash_needed, 2),
        "savings": round(savings_rate, 1),
        "risk": "预付费不可退款",
    }


def present_plans(plans: list[dict[str, Any]]) -> str:
    """Format plan comparison as a human-readable string."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("💰 JD Cloud 成本优化方案对比")
    lines.append("=" * 70)

    for plan in plans:
        lines.append("")
        lines.append(f"📋 {plan['name']}")
        lines.append(f"   ├─ 原价: ¥{plan['original']:.2f}")
        if "voucher_used" in plan:
            lines.append(f"   ├─ 代金券抵扣: ¥{plan['voucher_used']:.2f}")
        if "discounted" in plan:
            lines.append(f"   ├─ 折扣价: ¥{plan['discounted']:.2f}")
        lines.append(f"   ├─ 余额支付: ¥{plan['balance_used']:.2f}")
        lines.append(f"   ├─ 还需充值: ¥{plan['cash_needed']:.2f}")
        lines.append(f"   ├─ 节省率: {plan['savings']}%")
        lines.append(f"   └─ 风险: {plan['risk']}")

    best = max(plans, key=lambda p: p["savings"])
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"💡 推荐: {best['name']}（节省率 {best['savings']}%）")
    lines.append("=" * 70)

    return "\n".join(lines)


# ── mock data & demo ─────────────────────────────────────────────────────────


class _MockVoucher:
    """Minimal mock object matching SDK voucher shape."""

    def __init__(self, voucher_id: str, balance: float, expire_time: str, status: str):
        self.voucherId = voucher_id
        self.name = f"代金券-{voucher_id}"
        self.balance = str(balance)
        self.expireTime = expire_time
        self.status = status


def _mock_data() -> tuple[list[_MockVoucher], float, float, float]:
    vouchers = [
        _MockVoucher("v001", 2000.0, (datetime.now() + timedelta(days=15)).isoformat(), "active"),
        _MockVoucher("v002", 1000.0, (datetime.now() + timedelta(days=60)).isoformat(), "active"),
        _MockVoucher("v003", 500.0, (datetime.now() + timedelta(days=10)).isoformat(), "active"),
    ]
    return vouchers, 6000.0, 3000.0, 4800.0


def main() -> None:
    parser = argparse.ArgumentParser(description="JD Cloud cost optimization")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted table",
    )
    args = parser.parse_args()

    vouchers, original_price, balance, discounted_price = _mock_data()

    plans = [
        plan_a_voucher_first(vouchers, original_price, balance),
        plan_b_combined(vouchers, original_price, balance),
        plan_c_prepaid(original_price, discounted_price, balance),
    ]

    if args.json:
        print(json.dumps(plans, ensure_ascii=False, indent=2))
    else:
        print(present_plans(plans))


if __name__ == "__main__":
    main()
