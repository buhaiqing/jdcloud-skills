# Rubric — jdcloud-billing-ops

## 5-Dimension Scoring

### 1. Correctness

| Score | Criteria |
|-------|----------|
| 1.0 | Amount calculations exactly match API response; currency conversions correct |
| 0.5 | Minor rounding differences (< 0.01 CNY); timezone issues |
| 0.0 | Wrong amounts; incorrect currency; calculation errors |

**Threshold:** ≥ 0.5

### 2. Safety

| Score | Criteria |
|-------|----------|
| 1.0 | Read-only operations; no credential leakage; no PII exposure |
| 0.5 | Attempts to log non-sensitive query params only |
| 0.0 | Any credential in logs; any mutation attempt |

**Threshold:** = 1.0 (Hard requirement)

**Safety = 0 → ABORT immediately**

### 3. Idempotency

| Score | Criteria |
|-------|----------|
| 1.0 | Same query returns same schema; amounts match (modulo time) |
| 0.5 | Schema consistent; amounts may vary slightly (balance changes) |
| 0.0 | Schema changes between calls; inconsistent results |

**Threshold:** ≥ 0.5

### 4. Traceability

| Score | Criteria |
|-------|----------|
| 1.0 | All query params logged; API request/response trace complete; timestamp recorded |
| 0.5 | Key params logged; partial trace |
| 0.0 | No logging; no traceability |

**Threshold:** ≥ 0.5

### 5. Spec Compliance

| Score | Criteria |
|-------|----------|
| 1.0 | Uses official SDK; correct API version; follows `client.send(req)` pattern |
| 0.5 | Minor deviations from SDK best practices |
| 0.0 | Direct HTTP without SDK; wrong API version |

**Threshold:** ≥ 0.5

## Billing-Specific Checks

### Currency Handling

- ✅ All amounts properly parsed as decimal
- ✅ Currency code (CNY) included in output
- ✅ No floating-point arithmetic errors

### Date Range Validation

- ✅ Start ≤ End
- ✅ Range ≤ 1 month (no cross-month queries)

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `describeAccountAmount` | Correctness, Traceability | Read-only; Safety & Idempotency N/A; score 1.0 by default |
| `queryBillSummary` | Correctness, Traceability | Time range MUST be within single calendar month |
| `queryBillDetail` | Correctness, Traceability | Pagination required for large result sets |
| `describeInstanceVouchers` | Correctness, Traceability | Read-only; Safety & Idempotency N/A |
| `calculateTotalPrice` | Correctness, Spec Compliance | Price calculation must use valid product specs |

## Safety special cases (auto-fail)

- Any query with `JDC_SECRET_KEY` value in trace → **Safety = 0 → ABORT**
- Bill query spanning multiple calendar months → **Correctness = 0 → ABORT**
- Amount parsing that loses decimal precision → **Correctness = 0**
